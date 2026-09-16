const express = require("express");
const mongoose = require("mongoose");
const { ObjectId } = require("mongodb");

const {
    requireAuth,
    requireRole
} = require("../middleware/auth");

const router = express.Router();

// ============================================================
// NURSE DASHBOARD
// ============================================================

router.get(
    "/dashboard",
    requireAuth,
    requireRole("nurse"),
    async (req, res) => {
        try {
            const db = mongoose.connection.db;

            const usersCollection = db.collection("users");
            const appointmentsCollection = db.collection("appointments");
            const patientLogsCollection = db.collection("patient_logs");
            const shiftHandoffsCollection = db.collection("shift_handoffs");

            // ------------------------------------------------
            // BASIC COUNTS
            // ------------------------------------------------

            const totalPatients = await usersCollection.countDocuments({
                role: "patient"
            });

            const totalDoctors = await usersCollection.countDocuments({
                role: "doctor"
            });

            const myLogs = await patientLogsCollection.countDocuments({
                nurse_id: new ObjectId(req.session.user.id)
            });

            const incomingHandoffs = await shiftHandoffsCollection.countDocuments({
                to_nurse_id: new ObjectId(req.session.user.id),
                status: {
                    $in: ["sent", "pending"]
                }
            });

            // ------------------------------------------------
            // RECENT PATIENT LOGS
            // ------------------------------------------------

            const recentLogs = await patientLogsCollection
                .find({
                    nurse_id: new ObjectId(req.session.user.id)
                })
                .sort({
                    created_at: -1
                })
                .limit(10)
                .toArray();

            // ------------------------------------------------
            // UPCOMING APPOINTMENTS
            // Useful for knowing which patients are expected.
            // ------------------------------------------------

            const upcomingAppointments =
                await appointmentsCollection
                    .find({
                        status: {
                            $ne: "cancelled"
                        }
                    })
                    .sort({
                        appointment_datetime: 1
                    })
                    .limit(10)
                    .toArray();

            // ------------------------------------------------
            // RENDER DASHBOARD
            // ------------------------------------------------

            res.render("nurse/dashboard", {
                user: req.session.user,
                totalPatients,
                totalDoctors,
                myLogs,
                incomingHandoffs,
                recentLogs,
                upcomingAppointments
            });

        } catch (error) {

            console.error(
                "Error loading nurse dashboard:",
                error
            );

            res.status(500).send(
                "Unable to load nurse dashboard."
            );
        }
    }
);

// ============================================================
// PATIENTS
// ============================================================

router.get(
    "/patients",
    requireAuth,
    requireRole("nurse"),
    async (req, res) => {

        try {

            const db = mongoose.connection.db;

            const usersCollection =
                db.collection("users");

            const patients =
                await usersCollection
                    .find({
                        role: "patient"
                    })
                    .sort({
                        name: 1
                    })
                    .toArray();

            res.render(
                "nurse/patients",
                {
                    user: req.session.user,
                    patients
                }
            );

        } catch (error) {

            console.error(
                "Error loading nurse patients:",
                error
            );

            res.status(500).send(
                "Unable to load patients."
            );
        }
    }
);

// ============================================================
// NEW PATIENT LOG FORM
// ============================================================

router.get(
    "/patient-log/new",
    requireAuth,
    requireRole("nurse"),
    async (req, res) => {

        try {

            const db = mongoose.connection.db;

            const usersCollection =
                db.collection("users");

            const patients =
                await usersCollection
                    .find({
                        role: "patient"
                    })
                    .sort({
                        name: 1
                    })
                    .toArray();

            const doctors =
                await usersCollection
                    .find({
                        role: "doctor"
                    })
                    .sort({
                        name: 1
                    })
                    .toArray();

            res.render(
                "nurse/create-patient-log",
                {
                    user: req.session.user,
                    patients,
                    doctors
                }
            );

        } catch (error) {

            console.error(
                "Error loading patient log form:",
                error
            );

            res.status(500).send(
                "Unable to load patient log form."
            );
        }
    }
);

// ============================================================
// CREATE PATIENT LOG
// ============================================================

router.post(
    "/patient-log",
    requireAuth,
    requireRole("nurse"),
    async (req, res) => {

        try {

            const {
                patient_id,
                doctor_id,
                observations,
                symptoms,
                vital_notes,
                pain_comfort,
                medication_notes,
                additional_notes,
                priority
            } = req.body;

            // ------------------------------------------------
            // VALIDATION
            // ------------------------------------------------

            if (
                !patient_id ||
                !doctor_id
            ) {
                return res.status(400).send(
                    "Patient and doctor are required."
                );
            }

            if (
                !ObjectId.isValid(patient_id) ||
                !ObjectId.isValid(doctor_id)
            ) {
                return res.status(400).send(
                    "Invalid patient or doctor ID."
                );
            }

            const db = mongoose.connection.db;

            const usersCollection =
                db.collection("users");

            const patient =
                await usersCollection.findOne({
                    _id: new ObjectId(patient_id),
                    role: "patient"
                });

            const doctor =
                await usersCollection.findOne({
                    _id: new ObjectId(doctor_id),
                    role: "doctor"
                });

            if (!patient) {
                return res.status(404).send(
                    "Patient not found."
                );
            }

            if (!doctor) {
                return res.status(404).send(
                    "Doctor not found."
                );
            }

            // ------------------------------------------------
            // CREATE PATIENT LOG
            // ------------------------------------------------

            const patientLog = {

                patient_id: patient._id,

                patient_name: patient.name,

                patient_email: patient.email || "",

                nurse_id:
                    new ObjectId(req.session.user.id),

                nurse_name:
                    req.session.user.name,

                nurse_email:
                    req.session.user.email,

                doctor_id: doctor._id,

                doctor_name: doctor.name,

                doctor_email: doctor.email || "",

                observations:
                    (observations || "").trim(),

                symptoms:
                    (symptoms || "").trim(),

                vital_notes:
                    (vital_notes || "").trim(),

                pain_comfort:
                    (pain_comfort || "").trim(),

                medication_notes:
                    (medication_notes || "").trim(),

                additional_notes:
                    (additional_notes || "").trim(),

                priority:
                    priority || "normal",

                status: "sent",

                created_at: new Date(),

                updated_at: new Date()
            };

            const result =
                await db.collection("patient_logs")
                    .insertOne(patientLog);

            console.log(
                "Patient log created:",
                result.insertedId
            );

            res.redirect(
                "/nurse/patient-logs?created=1"
            );

        } catch (error) {

            console.error(
                "Error creating patient log:",
                error
            );

            res.status(500).send(
                "Unable to create patient log."
            );
        }
    }
);

// ============================================================
// NURSE PATIENT LOGS
// ============================================================

router.get(
    "/patient-logs",
    requireAuth,
    requireRole("nurse"),
    async (req, res) => {

        try {

            const db = mongoose.connection.db;

            const logs =
                await db.collection("patient_logs")
                    .find({
                        nurse_id:
                            new ObjectId(
                                req.session.user.id
                            )
                    })
                    .sort({
                        created_at: -1
                    })
                    .toArray();

            res.render(
                "nurse/patient-logs",
                {
                    user: req.session.user,
                    logs,
                    created: req.query.created === "1"
                }
            );

        } catch (error) {

            console.error(
                "Error loading patient logs:",
                error
            );

            res.status(500).send(
                "Unable to load patient logs."
            );
        }
    }
);

// ============================================================
// VIEW SINGLE PATIENT LOG
// ============================================================

router.get(
    "/patient-log/:id",
    requireAuth,
    requireRole("nurse"),
    async (req, res) => {

        try {

            if (!ObjectId.isValid(req.params.id)) {
                return res.status(400).send(
                    "Invalid patient log ID."
                );
            }

            const db = mongoose.connection.db;

            const log =
                await db.collection("patient_logs")
                    .findOne({
                        _id:
                            new ObjectId(req.params.id),

                        nurse_id:
                            new ObjectId(
                                req.session.user.id
                            )
                    });

            if (!log) {
                return res.status(404).send(
                    "Patient log not found."
                );
            }

            res.render(
                "nurse/patient-log",
                {
                    user: req.session.user,
                    log
                }
            );

        } catch (error) {

            console.error(
                "Error loading patient log:",
                error
            );

            res.status(500).send(
                "Unable to load patient log."
            );
        }
    }
);

// ============================================================
// SBAR PAGE
// ============================================================

router.get(
    "/sbar",
    requireAuth,
    requireRole("nurse"),
    async (req, res) => {

        try {

            const db = mongoose.connection.db;

            const usersCollection =
                db.collection("users");

            const patients =
                await usersCollection
                    .find({
                        role: "patient"
                    })
                    .sort({
                        name: 1
                    })
                    .toArray();

            const nurses =
                await usersCollection
                    .find({
                        role: "nurse",
                        _id: {
                            $ne:
                                new ObjectId(
                                    req.session.user.id
                                )
                        }
                    })
                    .sort({
                        name: 1
                    })
                    .toArray();

            res.render(
                "nurse/sbar",
                {
                    user: req.session.user,
                    patients,
                    nurses
                }
            );

        } catch (error) {

            console.error(
                "Error loading SBAR page:",
                error
            );

            res.status(500).send(
                "Unable to load SBAR page."
            );
        }
    }
);

// ============================================================
// SEND SBAR HANDOFF
// ============================================================

router.post(
    "/sbar",
    requireAuth,
    requireRole("nurse"),
    async (req, res) => {

        try {

            const {
                patient_id,
                receiving_nurse_id,
                situation,
                background,
                assessment,
                recommendation,
                priority
            } = req.body;

            if (
                !patient_id ||
                !receiving_nurse_id
            ) {
                return res.status(400).send(
                    "Patient and receiving nurse are required."
                );
            }

            if (
                !ObjectId.isValid(patient_id) ||
                !ObjectId.isValid(receiving_nurse_id)
            ) {
                return res.status(400).send(
                    "Invalid patient or nurse ID."
                );
            }

            const db = mongoose.connection.db;

            const usersCollection =
                db.collection("users");

            const patient =
                await usersCollection.findOne({
                    _id: new ObjectId(patient_id),
                    role: "patient"
                });

            const receivingNurse =
                await usersCollection.findOne({
                    _id:
                        new ObjectId(
                            receiving_nurse_id
                        ),
                    role: "nurse"
                });

            if (!patient) {
                return res.status(404).send(
                    "Patient not found."
                );
            }

            if (!receivingNurse) {
                return res.status(404).send(
                    "Receiving nurse not found."
                );
            }

            const handoff = {

                patient_id: patient._id,

                patient_name: patient.name,

                from_nurse_id:
                    new ObjectId(
                        req.session.user.id
                    ),

                from_nurse_name:
                    req.session.user.name,

                to_nurse_id:
                    receivingNurse._id,

                to_nurse_name:
                    receivingNurse.name,

                situation:
                    (situation || "").trim(),

                background:
                    (background || "").trim(),

                assessment:
                    (assessment || "").trim(),

                recommendation:
                    (recommendation || "").trim(),

                priority:
                    priority || "normal",

                status: "sent",

                created_at: new Date(),

                updated_at: new Date()
            };

            await db.collection("sbar_handoffs")
                .insertOne(handoff);

            res.redirect(
                "/nurse/handoff?sent=1"
            );

        } catch (error) {

            console.error(
                "Error sending SBAR:",
                error
            );

            res.status(500).send(
                "Unable to send SBAR handoff."
            );
        }
    }
);

// ============================================================
// SHIFT HANDOFF PAGE
// ============================================================

router.get(
    "/handoff",
    requireAuth,
    requireRole("nurse"),
    async (req, res) => {

        try {

            const db = mongoose.connection.db;

            const usersCollection =
                db.collection("users");

            const patients =
                await usersCollection
                    .find({
                        role: "patient"
                    })
                    .sort({
                        name: 1
                    })
                    .toArray();

            const nurses =
                await usersCollection
                    .find({
                        role: "nurse",
                        _id: {
                            $ne:
                                new ObjectId(
                                    req.session.user.id
                                )
                        }
                    })
                    .sort({
                        name: 1
                    })
                    .toArray();

            res.render(
                "nurse/shift-handoff",
                {
                    user: req.session.user,
                    patients,
                    nurses,
                    sent: req.query.sent === "1"
                }
            );

        } catch (error) {

            console.error(
                "Error loading shift handoff:",
                error
            );

            res.status(500).send(
                "Unable to load shift handoff."
            );
        }
    }
);

// ============================================================
// SEND SHIFT HANDOFF
// ============================================================

router.post(
    "/handoff",
    requireAuth,
    requireRole("nurse"),
    async (req, res) => {

        try {

            const {
                patient_ids,
                receiving_nurse_id,
                handoff_notes
            } = req.body;

            if (!receiving_nurse_id) {
                return res.status(400).send(
                    "Receiving nurse is required."
                );
            }

            if (!ObjectId.isValid(receiving_nurse_id)) {
                return res.status(400).send(
                    "Invalid receiving nurse."
                );
            }

            const selectedPatients =
                Array.isArray(patient_ids)
                    ? patient_ids
                    : patient_ids
                        ? [patient_ids]
                        : [];

            if (selectedPatients.length === 0) {
                return res.status(400).send(
                    "Select at least one patient."
                );
            }

            const invalidPatient =
                selectedPatients.some(
                    id => !ObjectId.isValid(id)
                );

            if (invalidPatient) {
                return res.status(400).send(
                    "Invalid patient selection."
                );
            }

            const db = mongoose.connection.db;

            const usersCollection =
                db.collection("users");

            const receivingNurse =
                await usersCollection.findOne({
                    _id:
                        new ObjectId(
                            receiving_nurse_id
                        ),
                    role: "nurse"
                });

            if (!receivingNurse) {
                return res.status(404).send(
                    "Receiving nurse not found."
                );
            }

            const patientObjectIds =
                selectedPatients.map(
                    id => new ObjectId(id)
                );

            const patients =
                await usersCollection
                    .find({
                        _id: {
                            $in: patientObjectIds
                        },
                        role: "patient"
                    })
                    .toArray();

            if (patients.length === 0) {
                return res.status(404).send(
                    "No valid patients found."
                );
            }

            const handoff = {

                from_nurse_id:
                    new ObjectId(
                        req.session.user.id
                    ),

                from_nurse_name:
                    req.session.user.name,

                to_nurse_id:
                    receivingNurse._id,

                to_nurse_name:
                    receivingNurse.name,

                patient_ids:
                    patients.map(
                        patient => patient._id
                    ),

                patient_names:
                    patients.map(
                        patient => patient.name
                    ),

                handoff_notes:
                    (handoff_notes || "").trim(),

                status: "sent",

                created_at: new Date(),

                updated_at: new Date()
            };

            await db.collection("shift_handoffs")
                .insertOne(handoff);

            res.redirect(
                "/nurse/handoff?sent=1"
            );

        } catch (error) {

            console.error(
                "Error sending shift handoff:",
                error
            );

            res.status(500).send(
                "Unable to send shift handoff."
            );
        }
    }
);

// ============================================================
// INCOMING HANDOFFS
// ============================================================

router.get(
    "/incoming-handoffs",
    requireAuth,
    requireRole("nurse"),
    async (req, res) => {

        try {

            const db = mongoose.connection.db;

            const nurseId =
                new ObjectId(
                    req.session.user.id
                );

            const shiftHandoffs =
                await db.collection("shift_handoffs")
                    .find({
                        to_nurse_id: nurseId
                    })
                    .sort({
                        created_at: -1
                    })
                    .toArray();

            const sbarHandoffs =
                await db.collection("sbar_handoffs")
                    .find({
                        to_nurse_id: nurseId
                    })
                    .sort({
                        created_at: -1
                    })
                    .toArray();

            res.render(
                "nurse/incoming-handoffs",
                {
                    user: req.session.user,
                    shiftHandoffs,
                    sbarHandoffs
                }
            );

        } catch (error) {

            console.error(
                "Error loading incoming handoffs:",
                error
            );

            res.status(500).send(
                "Unable to load incoming handoffs."
            );
        }
    }
);

module.exports = router;