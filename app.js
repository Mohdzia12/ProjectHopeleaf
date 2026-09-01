require("dotenv").config();

const express = require("express");
const session = require("express-session");
const { MongoStore } = require("connect-mongo");
const path = require("path");

// Database
const connectDB = require("./config/db");

// Routes
const authRoutes = require("./routes/authRoutes");
const patientRoutes = require("./routes/patientRoutes");
const doctorRoutes = require("./routes/doctorRoutes");
const adminRoutes = require("./routes/adminRoutes");
const medicalRecordsRoutes = require("./routes/medicalRecordsRoutes");
const toolsRoutes = require("./routes/toolsRoutes");
const prescriptionRoutes = require("./routes/prescriptionRoutes");
// ============================================================
// CREATE APP FIRST
// ============================================================

const app = express();

// ============================================================
// DATABASE
// ============================================================

connectDB();

// ============================================================
// VIEW ENGINE
// ============================================================

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

// ============================================================
// BODY PARSING
// ============================================================

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// ============================================================
// STATIC FILES
// ============================================================

app.use(express.static(path.join(__dirname, "public")));

// ============================================================
// SESSION
// ============================================================

app.use(
    session({
        secret: process.env.SESSION_SECRET || "hopeleaf_secret",

        resave: false,

        saveUninitialized: false,

        store: MongoStore.create({
            mongoUrl: process.env.MONGODB_URI,
            collectionName: "sessions"
        }),

        cookie: {
            maxAge: 1000 * 60 * 60 * 24,
            httpOnly: true
        }
    })
);

// ============================================================
// ROUTES
// ============================================================

app.use("/auth", authRoutes);

app.use("/patient", patientRoutes);

app.use("/doctor", doctorRoutes);

app.use("/admin", adminRoutes);

app.use("/medical-records", medicalRecordsRoutes);

app.use("/tools", toolsRoutes);

app.use("/prescriptions", prescriptionRoutes);

// ============================================================
// HOME ROUTE
// ============================================================

app.get("/", (req, res) => {

    // If user is logged in, send them
    // to their appropriate dashboard.

    if (req.session.user) {

        const role = req.session.user.role;

        if (role === "admin") {
            return res.redirect("/admin/dashboard");
        }

        if (role === "doctor") {
            return res.redirect("/doctor/dashboard");
        }

        if (role === "patient") {
            return res.redirect("/patient/dashboard");
        }
    }

    // No active session
    res.redirect("/auth/login");
});

// ============================================================
// 404 HANDLER
// ============================================================

app.use((req, res) => {
    res.status(404).send("Page not found.");
});

// ============================================================
// ERROR HANDLER
// ============================================================

app.use((err, req, res, next) => {

    console.error("Server error:", err);

    res.status(500).send("Something went wrong.");
});

// ============================================================
// START SERVER
// ============================================================

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {

    console.log("----------------------------------------");
    console.log("HopeLeaf server started");
    console.log(`http://localhost:${PORT}`);
    console.log("----------------------------------------");

});