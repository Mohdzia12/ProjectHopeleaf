const express = require("express");

const router = express.Router();

// ============================================================
// HOSPITAL WRITING PAD
// ============================================================

router.get("/writing-pad", (req, res) => {
    res.render("tools/writing-pad");
});

router.get("/Patient-log",(req,res) => {
res.render("tools/patient-log")
});

router.get("/SBAR",(req,res) => {
res.render("tools/sbar-handoff")
});



// ============================================================
// PRESCRIPTION DESIGNER
// ============================================================

router.get("/prescription", (req, res) => {
    res.render("tools/prescription");
});

// ============================================================
// CLINICAL NOTE FORMATTER
// ============================================================

router.get("/clinical-note", (req, res) => {
    res.render("tools/clinical-note");
});

// ============================================================
// BMI CALCULATOR
// ============================================================

router.get("/bmi", (req, res) => {
    res.render("tools/bmi");
});

// ============================================================
// MEDICATION SCHEDULE
// ============================================================

router.get("/medication-schedule", (req, res) => {
    res.render("tools/medication-schedule");
});

// ============================================================
// SYMPTOM JOURNAL
// ============================================================

router.get("/symptom-journal", (req, res) => {
    res.render("tools/symptom-journal");
});

module.exports = router;