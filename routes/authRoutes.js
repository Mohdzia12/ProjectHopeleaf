const express = require("express");

const {
    showRegister,
    register,
    showLogin,
    login,
    logout
} = require("../controllers/authController");

const router = express.Router();

router.get("/register", showRegister);
router.post("/register", register);

router.get("/login", showLogin);
router.post("/login", login);

router.get("/logout", logout);

module.exports = router;