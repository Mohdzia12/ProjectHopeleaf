
const express = require("express");
const router = express.Router();

const { ObjectId } = require("mongodb");
const mongoose = require("mongoose");
const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const {
    requireAuth,
    requireRole
} = require("../middleware/auth");

// ============================================================
// PRESCRIPTION PNG GENERATOR
// ============================================================

async function generatePrescriptionPNG({
    patientName,
    patientEmail,
    doctorName,
    doctorEmail,
    medicines,
    doctorComments,
    followUp
}) {
    const prescriptionDirectory = path.join(
        __dirname,
        "..",
        "public",
        "prescriptions"
    );

    if (!fs.existsSync(prescriptionDirectory)) {
        fs.mkdirSync(prescriptionDirectory, {
            recursive: true
        });
    }

    const filename =
        `prescription-${Date.now()}-${Math.random()
            .toString(36)
            .substring(2, 8)}.png`;

    const outputPath = path.join(
        prescriptionDirectory,
        filename
    );

    // --------------------------------------------------------
    // MEDICINE ROWS
    // --------------------------------------------------------

    const medicineRows = medicines.length
        ? medicines.map((medicine, index) => {
            const y = 440 + index * 70;

            return `
                <text
                    x="80"
                    y="${y}"
                    font-size="23"
                    fill="#1e293b"
                >
                    ${index + 1}. ${escapeXML(medicine.name)}
                </text>

                <text
                    x="420"
                    y="${y}"
                    font-size="21"
                    fill="#475569"
                >
                    ${escapeXML(medicine.dosage || "-")}
                </text>

                <text
                    x="650"
                    y="${y}"
                    font-size="21"
                    fill="#475569"
                >
                    ${escapeXML(medicine.frequency || "-")}
                </text>

                <text
                    x="900"
                    y="${y}"
                    font-size="21"
                    fill="#475569"
                >
                    ${escapeXML(medicine.duration || "-")}
                </text>
            `;
        }).join("")
        : `
            <text
                x="80"
                y="440"
                font-size="21"
                fill="#64748b"
            >
                No medicines prescribed.
            </text>
        `;

    const medicineHeight =
        Math.max(medicines.length, 1) * 70;

    const commentsY = 500 + medicineHeight;
    const followUpY = 650 + medicineHeight;

    const height =
        900 + medicineHeight;

    // --------------------------------------------------------
    // SVG
    // --------------------------------------------------------

    const svg = `
        <svg
            width="1200"
            height="${height}"
            xmlns="http://www.w3.org/2000/svg"
        >

            <!-- BACKGROUND -->

            <rect
                width="1200"
                height="${height}"
                fill="white"
            />

            <!-- HEADER -->

            <text
                x="80"
                y="75"
                font-size="42"
                font-weight="bold"
                fill="#059669"
            >
                HOPELEAF
            </text>

            <text
                x="80"
                y="115"
                font-size="20"
                fill="#64748b"
            >
                Clinical Prescription
            </text>

            <line
                x1="80"
                y1="145"
                x2="1120"
                y2="145"
                stroke="#d1d5db"
                stroke-width="2"
            />

            <!-- PATIENT -->

            <text
                x="80"
                y="200"
                font-size="17"
                fill="#64748b"
            >
                Patient
            </text>

            <text
                x="80"
                y="232"
                font-size="24"
                font-weight="bold"
                fill="#1e293b"
            >
                ${escapeXML(patientName || "-")}
            </text>

            <text
                x="500"
                y="200"
                font-size="17"
                fill="#64748b"
            >
                Patient Email
            </text>

            <text
                x="500"
                y="232"
                font-size="21"
                fill="#334155"
            >
                ${escapeXML(patientEmail || "-")}
            </text>

            <!-- DOCTOR -->

            <text
                x="80"
                y="280"
                font-size="17"
                fill="#64748b"
            >
                Doctor
            </text>

            <text
                x="80"
                y="312"
                font-size="22"
                font-weight="bold"
                fill="#1e293b"
            >
                Dr. ${escapeXML(doctorName || "-")}
            </text>

            <text
                x="500"
                y="280"
                font-size="17"
                fill="#64748b"
            >
                Doctor Email
            </text>

            <text
                x="500"
                y="312"
                font-size="21"
                fill="#334155"
            >
                ${escapeXML(doctorEmail || "-")}
            </text>

            <text
                x="80"
                y="360"
                font-size="17"
                fill="#64748b"
            >
                Date
            </text>

            <text
                x="80"
                y="392"
                font-size="21"
                fill="#334155"
            >
                ${new Date().toLocaleDateString("en-IN")}
            </text>

            <!-- MEDICINES -->

            <text
                x="80"
                y="425"
                font-size="26"
                font-weight="bold"
                fill="#1e293b"
            >
                Medicines
            </text>

            <text
                x="80"
                y="455"
                font-size="16"
                fill="#64748b"
            >
                Medicine
            </text>

            <text
                x="420"
                y="455"
                font-size="16"
                fill="#64748b"
            >
                Dosage
            </text>

            <text
                x="650"
                y="455"
                font-size="16"
                fill="#64748b"
            >
                Frequency
            </text>

            <text
                x="900"
                y="455"
                font-size="16"
                fill="#64748b"
            >
                Duration
            </text>

            ${medicineRows}

            <!-- DOCTOR COMMENTS -->

            <text
                x="80"
                y="${commentsY}"
                font-size="26"
                font-weight="bold"
                fill="#1e293b"
            >
                Doctor's Instructions
            </text>

            <text
                x="80"
                y="${commentsY + 40}"
                font-size="21"
                fill="#475569"
            >
                ${escapeXML(
                    doctorComments ||
                    "No additional instructions."
                )}
            </text>

            <!-- FOLLOW UP -->

            <text
                x="80"
                y="${followUpY}"
                font-size="26"
                font-weight="bold"
                fill="#1e293b"
            >
                Follow-up
            </text>

            <text
                x="80"
                y="${followUpY + 40}"
                font-size="21"
                fill="#475569"
            >
                Date: ${escapeXML(
                    followUp?.date || "-"
                )}
            </text>

            <text
                x="400"
                y="${followUpY + 40}"
                font-size="21"
                fill="#475569"
            >
                Type: ${escapeXML(
                    followUp?.type || "-"
                )}
            </text>

            <text
                x="80"
                y="${followUpY + 80}"
                font-size="21"
                fill="#475569"
            >
                ${escapeXML(
                    followUp?.instructions ||
                    "No follow-up instructions."
                )}
            </text>

            <!-- FOOTER -->

            <line
                x1="80"
                y1="${height - 80}"
                x2="1120"
                y2="${height - 80}"
                stroke="#e2e8f0"
                stroke-width="2"
            />

            <text
                x="80"
                y="${height - 40}"
                font-size="16"
                fill="#94a3b8"
            >
                Generated by HopeLeaf
            </text>

        </svg>
    `;

    await sharp(Buffer.from(svg))
        .png()
        .toFile(outputPath);

    return {
        filename,
        filePath: `/prescriptions/${filename}`,
        physicalPath: outputPath
    };
}

// ============================================================
// XML ESCAPE
// ============================================================

function escapeXML(value) {
    return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&apos;");
}

// ============================================================
// DOCTOR DASHBOARD
// ============================================================

router.get(
    "/dashboard",
    requireAuth,
    requireRole("doctor"),
    async (req, res) => {
        try {
            const db = mongoose.connection.db;

            const appointmentsCollection =
                db.collection("appointments");

            const doctorId =
                new ObjectId(req.session.user.id);

            const appointments =
                await appointmentsCollection
                    .find({
                        doctor_id: doctorId,
                        status: {
                            $ne: "cancelled"
                        }
                    })
                    .sort({
                        created_at: -1,
                        appointment_datetime: 1
                    })
                    .toArray();

            const now = new Date();

            const upcomingAppointments =
                appointments.filter((appointment) => {
                    if (!appointment.appointment_datetime) {
                        return true;
                    }

                    return new Date(
                        appointment.appointment_datetime
                    ) >= now;
                });

            const recentAppointments =
                appointments.slice(0, 10);

            const totalAppointments =
                appointments.length;

            const upcomingCount =
                upcomingAppointments.length;

            const completedCount =
                appointments.filter(
                    appointment =>
                        appointment.status === "completed"
                ).length;

            res.render(
                "doctor/dashboard",
                {
                    user: req.session.user,
                    appointments,
                    upcomingAppointments,
                    recentAppointments,
                    totalAppointments,
                    upcomingCount,
                    completedCount
                }
            );

        } catch (error) {
            console.error(
                "Error loading doctor dashboard:",
                error
            );

            res.status(500).send(
                "Unable to load doctor dashboard."
            );
        }
    }
);

// ============================================================
// DOCTOR CONSULTATION PAGE
// ============================================================

router.get(
    "/appointment/:id",
    requireAuth,
    requireRole("doctor"),
    async (req, res) => {
        try {
            const db = mongoose.connection.db;

            const appointmentsCollection =
                db.collection("appointments");

            if (!ObjectId.isValid(req.params.id)) {
                return res
                    .status(400)
                    .send("Invalid appointment ID.");
            }

            const appointmentId =
                new ObjectId(req.params.id);

            const doctorId =
                new ObjectId(req.session.user.id);

            const appointment =
                await appointmentsCollection.findOne({
                    _id: appointmentId,
                    doctor_id: doctorId
                });

            if (!appointment) {
                return res
                    .status(404)
                    .send("Appointment not found.");
            }

            res.render(
                "doctor/appointment",
                {
                    user: req.session.user,
                    appointment
                }
            );

        } catch (error) {
            console.error(
                "Error loading consultation:",
                error
            );

            res.status(500).send(
                "Unable to load consultation."
            );
        }
    }
);

// ============================================================
// CLINICAL NOTE PAGE
// ============================================================

router.get(
    "/appointment/:id/note",
    requireAuth,
    requireRole("doctor"),
    async (req, res) => {
        try {
            const db = mongoose.connection.db;

            const appointmentsCollection =
                db.collection("appointments");

            if (!ObjectId.isValid(req.params.id)) {
                return res
                    .status(400)
                    .send("Invalid appointment ID.");
            }

            const appointmentId =
                new ObjectId(req.params.id);

            const doctorId =
                new ObjectId(req.session.user.id);

            const appointment =
                await appointmentsCollection.findOne({
                    _id: appointmentId,
                    doctor_id: doctorId
                });

            if (!appointment) {
                return res
                    .status(404)
                    .send("Appointment not found.");
            }

            res.render(
                "doctor/clinical-note",
                {
                    user: req.session.user,
                    appointment
                }
            );

        } catch (error) {
            console.error(
                "Error loading clinical note:",
                error
            );

            res.status(500).send(
                "Unable to load clinical note."
            );
        }
    }
);

// ============================================================
// SAVE CLINICAL NOTE
// ============================================================

router.post(
    "/appointment/:id/note",
    requireAuth,
    requireRole("doctor"),
    async (req, res) => {
        try {
            const db = mongoose.connection.db;

            const appointmentsCollection =
                db.collection("appointments");

            const prescriptionsCollection =
                db.collection("prescriptions");

            // ------------------------------------------------
            // VALIDATE APPOINTMENT ID
            // ------------------------------------------------

            if (!ObjectId.isValid(req.params.id)) {
                return res
                    .status(400)
                    .send("Invalid appointment ID.");
            }

            const appointmentId =
                new ObjectId(req.params.id);

            const doctorId =
                new ObjectId(req.session.user.id);

            // ------------------------------------------------
            // FIND APPOINTMENT
            // ------------------------------------------------

            const appointment =
                await appointmentsCollection.findOne({
                    _id: appointmentId,
                    doctor_id: doctorId
                });

            if (!appointment) {
                return res
                    .status(404)
                    .send("Appointment not found.");
            }

            // ------------------------------------------------
            // PATIENT INFORMATION
            // ------------------------------------------------

            const patientId =
                appointment.patient_id;

            const patientName =
                appointment.patient_name ||
                appointment.patientName ||
                "Patient";

            const patientEmail =
                appointment.patient_email ||
                appointment.patientEmail ||
                "";

            // ------------------------------------------------
            // DOCTOR INFORMATION
            // ------------------------------------------------

            const doctorName =
                req.session.user.name ||
                "Doctor";

            const doctorEmail =
                req.session.user.email ||
                "";

            // ------------------------------------------------
            // FORM FIELDS
            // ------------------------------------------------

            const doctorComments =
                (
                    req.body.doctor_comments ||
                    ""
                ).trim();

            const followUpDate =
                (
                    req.body.follow_up_date ||
                    ""
                ).trim();

            const followUpType =
                (
                    req.body.follow_up_type ||
                    ""
                ).trim();

            const followUpInstructions =
                (
                    req.body.follow_up_instructions ||
                    ""
                ).trim();

            // ------------------------------------------------
            // MEDICINES
            // ------------------------------------------------

            let medicines = [];

            if (
                Array.isArray(
                    req.body.medicine_name
                )
            ) {
                const names =
                    req.body.medicine_name;

                const dosages =
                    req.body.medicine_dosage || [];

                const frequencies =
                    req.body.medicine_frequency || [];

                const durations =
                    req.body.medicine_duration || [];

                for (
                    let i = 0;
                    i < names.length;
                    i++
                ) {
                    const name =
                        (
                            names[i] || ""
                        ).trim();

                    const dosage =
                        (
                            dosages[i] || ""
                        ).trim();

                    const frequency =
                        (
                            frequencies[i] || ""
                        ).trim();

                    const duration =
                        (
                            durations[i] || ""
                        ).trim();

                    if (name) {
                        medicines.push({
                            name,
                            dosage,
                            frequency,
                            duration
                        });
                    }
                }

            } else if (
                req.body.medicine_name
            ) {
                const name =
                    req.body.medicine_name.trim();

                if (name) {
                    medicines.push({
                        name,
                        dosage: (
                            req.body.medicine_dosage ||
                            ""
                        ).trim(),
                        frequency: (
                            req.body.medicine_frequency ||
                            ""
                        ).trim(),
                        duration: (
                            req.body.medicine_duration ||
                            ""
                        ).trim()
                    });
                }
            }

            // ------------------------------------------------
            // CLINICAL NOTE
            // ------------------------------------------------

            const clinicalNote = {
                doctor_id: doctorId,

                doctor_name: doctorName,

                doctor_email: doctorEmail,

                doctor_comments:
                    doctorComments,

                medicines,

                follow_up: {
                    date: followUpDate,
                    type: followUpType,
                    instructions:
                        followUpInstructions
                },

                updated_at: new Date()
            };

            // ------------------------------------------------
            // SAVE CLINICAL NOTE TO APPOINTMENT
            // ------------------------------------------------

            await appointmentsCollection.updateOne(
                {
                    _id: appointmentId,
                    doctor_id: doctorId
                },
                {
                    $set: {
                        clinical_note:
                            clinicalNote
                    }
                }
            );

            // =================================================
            // GENERATE PRESCRIPTION PNG
            // =================================================

            const generatedPrescription =
                await generatePrescriptionPNG({
                    patientName,
                    patientEmail,
                    doctorName,
                    doctorEmail,
                    medicines,
                    doctorComments,
                    followUp: {
                        date: followUpDate,
                        type: followUpType,
                        instructions:
                            followUpInstructions
                    }
                });

            // =================================================
            // REMOVE OLD PRESCRIPTION FILES FOR THIS
            // APPOINTMENT
            // =================================================

            const oldPrescriptions =
                await prescriptionsCollection
                    .find({
                        appointment_id:
                            appointmentId
                    })
                    .toArray();

            for (
                const oldPrescription
                of oldPrescriptions
            ) {
                if (
                    oldPrescription.stored_filename &&
                    oldPrescription.stored_filename !==
                        generatedPrescription.filename
                ) {
                    const oldFilePath =
                        path.join(
                            __dirname,
                            "..",
                            "public",
                            "prescriptions",
                            oldPrescription.stored_filename
                        );

                    if (
                        fs.existsSync(oldFilePath)
                    ) {
                        try {
                            fs.unlinkSync(
                                oldFilePath
                            );
                        } catch (fileError) {
                            console.error(
                                "Could not delete old prescription file:",
                                fileError
                            );
                        }
                    }
                }
            }

            // =================================================
            // REMOVE OLD DATABASE PRESCRIPTION RECORD
            // =================================================

            await prescriptionsCollection.deleteMany({
                appointment_id:
                    appointmentId
            });

            // =================================================
            // SAVE NEW PRESCRIPTION
            // =================================================

            const prescription = {
                appointment_id:
                    appointmentId,

                doctor_id:
                    doctorId,

                doctor_name:
                    doctorName,

                doctor_email:
                    doctorEmail,

                patient_id:
                    patientId,

                patient_name:
                    patientName,

                patient_email:
                    patientEmail,

                original_filename:
                    `Prescription-${patientName}.png`,

                stored_filename:
                    generatedPrescription.filename,

                file_path:
                    generatedPrescription.filePath,

                description:
                    "Clinical prescription generated from doctor's clinical note.",

                medicines,

                doctor_comments:
                    doctorComments,

                follow_up: {
                    date: followUpDate,
                    type: followUpType,
                    instructions:
                        followUpInstructions
                },

                uploaded_at:
                    new Date(),

                source:
                    "clinical-note"
            };

            await prescriptionsCollection.insertOne(
                prescription
            );

            // =================================================
            // REDIRECT
            // =================================================

            res.redirect(
                `/doctor/appointment/${appointmentId}/note?saved=1&prescription=1`
            );

        } catch (error) {
            console.error(
                "Error saving clinical note:",
                error
            );

            res.status(500).send(
                "Unable to save clinical note and prescription."
            );
        }
    }
);

// ==========================================
// PATIENT LOGS FROM NURSES
// ==========================================

router.get(
    "/patient-logs",
    requireAuth,
    requireRole("doctor"),
    async (req, res) => {
        try {
            const db = mongoose.connection.db;

            const logs = await db
                .collection("patient_logs")
                .find({
                    doctor_id: new ObjectId(req.session.user.id)
                })
                .sort({ created_at: -1 })
                .toArray();

            res.render("doctor/patient-logs", {
                user: req.session.user,
                logs
            });

        } catch (error) {
            console.error("Doctor patient logs error:", error);
            res.status(500).send("Unable to load patient logs.");
        }
    }
);


router.get(
    "/patient-log/:id",
    requireAuth,
    requireRole("doctor"),
    async (req, res) => {
        try {
            const { id } = req.params;

            if (!ObjectId.isValid(id)) {
                return res.status(400).send("Invalid patient log ID.");
            }

            const db = mongoose.connection.db;

            const log = await db.collection("patient_logs").findOne({
                _id: new ObjectId(id),
                doctor_id: new ObjectId(req.session.user.id)
            });

            if (!log) {
                return res.status(404).send("Patient log not found.");
            }

            res.render("doctor/patient-log", {
                user: req.session.user,
                log
            });

        } catch (error) {
            console.error("Doctor patient log detail error:", error);
            res.status(500).send("Unable to load patient log.");
        }
    }
);
module.exports = router;

