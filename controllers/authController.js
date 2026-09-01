const User = require("../models/User");
const bcrypt = require("bcryptjs");

const showRegister = (req, res) => {
    res.render("auth/register");
};

const register = async (req, res) => {
    try {
        const { name, email, password, role } = req.body;

        if (!name || !email || !password || !role) {
            return res.send("Please fill in all fields.");
        }

        if (!["doctor", "patient"].includes(role)) {
            return res.status(400).send("Invalid registration role.");
        }

        const existingUser = await User.findOne({ email });

        if (existingUser) {
            return res.status(400).send("An account with this email already exists.");
        }

        const hashedPassword = await bcrypt.hash(password, 10);

        await User.create({
            name,
            email,
            password: hashedPassword,
            role
        });

        res.redirect("/auth/login");
    } catch (error) {
        console.error("Registration error:", error);
        res.status(500).send("Registration failed.");
    }
};

const showLogin = (req, res) => {
    res.render("auth/login");
};

const login = async (req, res) => {
    try {
        const { email, password } = req.body;

        if (!email || !password) {
            return res.send("Please enter your email and password.");
        }

        const user = await User.findOne({ email });

        if (!user) {
            return res.status(401).send("Invalid email or password.");
        }

        const passwordMatch = await bcrypt.compare(password, user.password);

        if (!passwordMatch) {
            return res.status(401).send("Invalid email or password.");
        }

        req.session.user = {
            id: user._id,
            name: user.name,
            email: user.email,
            role: user.role
        };

        if (user.role === "admin") {
            return res.redirect("/admin/dashboard");
        }

        if (user.role === "doctor") {
            return res.redirect("/doctor/dashboard");
        }

        if (user.role === "patient") {
            return res.redirect("/patient/dashboard");
        }

        res.status(400).send("Invalid user role.");
    } catch (error) {
        console.error("Login error:", error);
        res.status(500).send("Login failed.");
    }
};

const logout = (req, res) => {
    req.session.destroy((error) => {
        if (error) {
            console.error("Logout error:", error);
            return res.status(500).send("Logout failed.");
        }

        res.redirect("/auth/login");
    });
};

module.exports = {
    showRegister,
    register,
    showLogin,
    login,
    logout
};