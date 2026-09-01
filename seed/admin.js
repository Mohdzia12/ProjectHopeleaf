require("dotenv").config();

const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");

const User = require("../models/User");

const createAdmin = async () => {
    try {
        await mongoose.connect(process.env.MONGODB_URI);

        console.log("Connected to MongoDB");

        const existingAdmin = await User.findOne({
            role: "admin"
        });

        if (existingAdmin) {
            console.log("Admin account already exists.");
            process.exit(0);
        }

        const hashedPassword = await bcrypt.hash("admin123", 10);

        await User.create({
            name: "HopeLeaf Admin",
            email: "admin@hopeleaf.com",
            password: hashedPassword,
            role: "admin"
        });

        console.log("Admin account created successfully.");
        console.log("Email: admin@hopeleaf.com");
        console.log("Password: admin123");

        process.exit(0);

    } catch (error) {
        console.error("Admin seed failed:", error);
        process.exit(1);
    }
};

createAdmin();