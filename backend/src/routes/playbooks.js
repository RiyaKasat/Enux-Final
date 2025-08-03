const express = require('express');
const db = require('../config/database');

const router = express.Router();

// GET /api/playbooks/:id - Get playbook details with blocks
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    // Get upload/playbook info
    const uploadResult = await db.query(
      'SELECT * FROM uploads WHERE id = $1',
      [id]
    );

    if (uploadResult.rows.length === 0) {
      return res.status(404).json({ error: 'Playbook not found' });
    }

    const upload = uploadResult.rows[0];

    // Get all content blocks
    const blocksResult = await db.query(`
      SELECT * FROM content_blocks 
      WHERE upload_id = $1 
      ORDER BY created_at ASC
    `, [id]);

    // Get asset mapping suggestions
    const mappingsResult = await db.query(`
      SELECT cb.id as block_id, am.* 
      FROM content_blocks cb
      LEFT JOIN asset_mappings am ON cb.id = am.block_id
      WHERE cb.upload_id = $1
    `, [id]);

    res.json({
      playbook: upload,
      blocks: blocksResult.rows,
      asset_mappings: mappingsResult.rows
    });

  } catch (error) {
    console.error('Playbook fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch playbook' });
  }
});

// POST /api/playbooks/:id/approve-mapping - Approve asset mapping
router.post('/:id/approve-mapping', async (req, res) => {
  try {
    const { id } = req.params;
    const { block_mappings } = req.body;

    // Start transaction
    await db.query('BEGIN');

    try {
      // Update asset mappings
      for (const mapping of block_mappings) {
        await db.query(`
          UPDATE content_blocks 
          SET final_asset_type = $1, mapping_approved = true
          WHERE id = $2 AND upload_id = $3
        `, [mapping.asset_type, mapping.block_id, id]);
      }

      // Update upload status
      await db.query(
        'UPDATE uploads SET status = $1 WHERE id = $2',
        ['mapped', id]
      );

      await db.query('COMMIT');

      res.json({
        success: true,
        message: 'Asset mapping approved successfully'
      });

    } catch (error) {
      await db.query('ROLLBACK');
      throw error;
    }

  } catch (error) {
    console.error('Mapping approval error:', error);
    res.status(500).json({ error: 'Failed to approve mapping' });
  }
});

// GET /api/playbooks - List all playbooks
router.get('/', async (req, res) => {
  try {
    const { page = 1, limit = 10, status } = req.query;
    const offset = (page - 1) * limit;

    let query = `
      SELECT u.*, COUNT(cb.id) as block_count
      FROM uploads u
      LEFT JOIN content_blocks cb ON u.id = cb.upload_id
    `;
    
    const params = [];
    if (status) {
      query += ` WHERE u.status = $1`;
      params.push(status);
    }

    query += `
      GROUP BY u.id
      ORDER BY u.created_at DESC
      LIMIT $${params.length + 1} OFFSET $${params.length + 2}
    `;
    
    params.push(limit, offset);

    const result = await db.query(query, params);

    res.json({
      playbooks: result.rows,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total: result.rows.length
      }
    });

  } catch (error) {
    console.error('Playbooks list error:', error);
    res.status(500).json({ error: 'Failed to fetch playbooks' });
  }
});

module.exports = router;
