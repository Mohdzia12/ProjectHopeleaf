const express = require("express");
const router = express.Router();
const crypto = require("crypto");
const { ObjectId } = require("mongodb");
const mongoose = require("mongoose");

const { requireAuth, requireRole } = require("../middleware/auth");


// ============================================================
// CREATE SIGNED PATIENT TOKEN
// ============================================================

function createPatientToken(userId) {
    const payload = JSON.stringify({
        id: userId,
        exp: Date.now() + (10 * 60 * 1000) // 10 minutes
    });

    const encodedPayload = Buffer
        .from(payload)
        .toString("base64url");

    const signature = crypto
        .createHmac(
            "sha256",
            process.env.SESSION_SECRET
        )
        .update(encodedPayload)
        .digest("base64url");

    return `${encodedPayload}.${signature}`;
}


// ============================================================
// PATIENT DASHBOARD
// ============================================================

router.get(
    "/dashboard",
    requireAuth,
    requireRole("patient"),
    async (req, res) => {

        try {

            const db = mongoose.connection.db;

            const appointmentsCollection =
                db.collection("appointments");


            // ------------------------------------------------
            // GET PATIENT APPOINTMENTS
            // ------------------------------------------------

            const appointments =
                await appointmentsCollection
                    .find({
                        patient_id: new ObjectId(
                            req.session.user.id
                        )
                    })
                    .sort({
                        appointment_datetime: 1
                    })
                    .toArray();


            // ------------------------------------------------
            // CREATE SHORT-LIVED IDENTITY TOKEN
            // ------------------------------------------------

            const patientToken =
                createPatientToken(
                    req.session.user.id
                );


            // ------------------------------------------------
            // RENDER DASHBOARD
            // ------------------------------------------------

            res.render("patient/dashboard", {

                user: req.session.user,

                appointments: appointments,

                patientToken: patientToken

            });

        } catch (error) {

            console.error(
                "Error loading patient dashboard:",
                error
            );

            res.render("patient/dashboard", {

                user: req.session.user,

                appointments: [],

                patientToken: null

            });
        }
    }
);


module.exports = router;