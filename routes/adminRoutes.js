const express = require("express");

const { requireRole } = require("../middleware/auth");

const router = express.Router();

router.get("/dashboard", requireRole("admin"), (req, res) => {
    res.render("admin/dashboard", {
        user: req.session.user
    });
});

module.exports = router;