const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const { v4: uuidv4 } = require('uuid');
const axios = require('axios');

const db = require('../config/database');
const { extractContent } = require('../services/contentExtractor');

const router = express.Router();

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadDir = process.env.UPLOAD_DIR || './uploads';
    try {
      await fs.mkdir(uploadDir, { recursive: true });
      cb(null, uploadDir);
    } catch (error) {
      cb(error);
    }
  },
  filename: (req, file, cb) => {
    const uniqueName = `${uuidv4()}_${file.originalname}`;
    cb(null, uniqueName);
  }
});

const upload = multer({
  storage,
  limits: {
    fileSize: parseInt(process.env.MAX_FILE_SIZE) || 10 * 1024 * 1024 // 10MB
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['.pdf', '.txt', '.md', '.docx'];
    const fileExt = path.extname(file.originalname).toLowerCase();
    
    if (allowedTypes.includes(fileExt)) {
      cb(null, true);
    } else {
      cb(new Error(`File type ${fileExt} not allowed`), false);
    }
  }
});

// POST /api/upload/file - Upload and process file
router.post('/file', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const { title, description, tags } = req.body;
    const uploadId = uuidv4();

    // Step 1: Store initial upload record
    const uploadQuery = `
      INSERT INTO uploads (id, filename, original_name, file_path, file_size, mime_type, status, created_at)
      VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
      RETURNING *
    `;
    
    const uploadResult = await db.query(uploadQuery, [
      uploadId,
      req.file.filename,
      req.file.originalname,
      req.file.path,
      req.file.size,
      req.file.mimetype,
      'processing'
    ]);

    // Step 2: Extract content using AI service
    try {
      const extractedData = await extractContent(req.file.path, req.file.mimetype);
      
      // Step 3: Store extracted blocks
      for (const block of extractedData.blocks) {
        await db.query(`
          INSERT INTO content_blocks (id, upload_id, type, content, confidence_score, suggested_asset_type, created_at)
          VALUES ($1, $2, $3, $4, $5, $6, NOW())
        `, [
          uuidv4(),
          uploadId,
          block.type,
          block.content,
          block.confidence_score || 0.8,
          block.suggested_asset_type
        ]);
      }

      // Step 4: Update upload status
      await db.query(
        'UPDATE uploads SET status = $1, processed_at = NOW() WHERE id = $2',
        ['completed', uploadId]
      );

      res.json({
        success: true,
        upload_id: uploadId,
        message: 'File uploaded and processed successfully',
        blocks_extracted: extractedData.blocks.length,
        redirect_url: `/playbook/${uploadId}`
      });

    } catch (aiError) {
      console.error('AI processing error:', aiError);
      
      // Update status to failed
      await db.query(
        'UPDATE uploads SET status = $1, error_message = $2 WHERE id = $3',
        ['failed', aiError.message, uploadId]
      );

      res.status(500).json({
        error: 'Failed to process file content',
        upload_id: uploadId
      });
    }

  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: 'Upload failed', details: error.message });
  }
});

// POST /api/upload/url - Process external URL
router.post('/url', async (req, res) => {
  try {
    const { url, title, description } = req.body;
    
    if (!url) {
      return res.status(400).json({ error: 'URL is required' });
    }

    const uploadId = uuidv4();

    // Store URL upload record
    await db.query(`
      INSERT INTO uploads (id, source_url, original_name, status, created_at)
      VALUES ($1, $2, $3, $4, NOW())
    `, [uploadId, url, title || 'URL Import', 'processing']);

    // Extract content from URL
    const extractedData = await extractContent(url, 'url');
    
    // Store extracted blocks
    for (const block of extractedData.blocks) {
      await db.query(`
        INSERT INTO content_blocks (id, upload_id, type, content, confidence_score, suggested_asset_type, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, NOW())
      `, [
        uuidv4(),
        uploadId,
        block.type,
        block.content,
        block.confidence_score || 0.8,
        block.suggested_asset_type
      ]);
    }

    await db.query(
      'UPDATE uploads SET status = $1, processed_at = NOW() WHERE id = $2',
      ['completed', uploadId]
    );

    res.json({
      success: true,
      upload_id: uploadId,
      message: 'URL processed successfully',
      blocks_extracted: extractedData.blocks.length
    });

  } catch (error) {
    console.error('URL processing error:', error);
    res.status(500).json({ error: 'Failed to process URL', details: error.message });
  }
});

// GET /api/upload/:id/status - Check upload status
router.get('/:id/status', async (req, res) => {
  try {
    const { id } = req.params;
    
    const result = await db.query(
      'SELECT * FROM uploads WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Upload not found' });
    }

    const upload = result.rows[0];
    
    // Get blocks count if completed
    let blocksCount = 0;
    if (upload.status === 'completed') {
      const blocksResult = await db.query(
        'SELECT COUNT(*) as count FROM content_blocks WHERE upload_id = $1',
        [id]
      );
      blocksCount = parseInt(blocksResult.rows[0].count);
    }

    res.json({
      ...upload,
      blocks_extracted: blocksCount
    });

  } catch (error) {
    console.error('Status check error:', error);
    res.status(500).json({ error: 'Failed to check status' });
  }
});

module.exports = router;
