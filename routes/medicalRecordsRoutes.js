const express = require("express");

const router = express.Router();


// ============================================================
// MEDICAL RECORDS LOGIN PAGE
// ============================================================

router.get("/", (req, res) => {
    res.render("medical-records", {
        error: null,
        records: null,
        patient: null
    });
});


// ============================================================
// MEDICAL RECORDS LOGIN
// ============================================================

router.post("/", async (req, res) => {

    try {

        const email =
            (req.body.email || "").trim().toLowerCase();

        const password =
            (req.body.password || "").trim();


        // ----------------------------------------------------
        // BASIC VALIDATION
        // ----------------------------------------------------

        if (!email || !password) {

            return res.render("medical-records", {
                error: "Please enter your email and password.",
                records: null,
                patient: null
            });
        }


        // ----------------------------------------------------
        // DATABASE
        // ----------------------------------------------------

        const mongoose = require("mongoose");

        const db = mongoose.connection.db;

        const usersCollection =
            db.collection("users");

        const appointmentsCollection =
            db.collection("appointments");


        // ----------------------------------------------------
        // FIND PATIENT
        // ----------------------------------------------------

        const patient =
            await usersCollection.findOne({
                email: email,
                role: "patient"
            });


        if (!patient) {

            return res.render("medical-records", {
                error: "Invalid email or password.",
                records: null,
                patient: null
            });
        }


        // ----------------------------------------------------
        // PASSWORD CHECK
        //
        // This supports the common password field names.
        // We will align this with your actual auth system
        // once we inspect its login code.
        // ----------------------------------------------------

        const bcrypt =
            require("bcryptjs");

        const storedPassword =
            patient.password ||
            patient.passwordHash ||
            patient.password_hash;


        if (!storedPassword) {

            return res.render("medical-records", {
                error:
                    "This patient account does not have a usable password record.",
                records: null,
                patient: null
            });
        }


        const passwordMatches =
            await bcrypt.compare(
                password,
                storedPassword
            );


        if (!passwordMatches) {

            return res.render("medical-records", {
                error: "Invalid email or password.",
                records: null,
                patient: null
            });
        }


        // ----------------------------------------------------
        // GET PATIENT MEDICAL RECORDS
        //
        // Records are retrieved directly from MongoDB.
        // Nothing here depends on patientRoutes.js.
        // ----------------------------------------------------

        const records =
            await appointmentsCollection
                .find({
                    patient_id: patient._id
                })
                .sort({
                    appointment_datetime: -1,
                    created_at: -1
                })
                .toArray();


        // ----------------------------------------------------
        // RENDER RECORDS
        // ----------------------------------------------------

        return res.render(
            "medical-records",
            {
                error: null,

                patient: {
                    name: patient.name,
                    email: patient.email
                },

                records: records
            }
        );

    } catch (error) {

        console.error(
            "Medical records error:",
            error
        );

        return res.status(500).render(
            "medical-records",
            {
                error:
                    "Unable to retrieve medical records.",
                records: null,
                patient: null
            }
        );
    }
});


module.exports = router;