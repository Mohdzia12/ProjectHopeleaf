const express = require("express");
const router = express.Router();

const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");
const multer = require("multer");
const path = require("path");
const fs = require("fs");

// ============================================================
// UPLOAD CONFIGURATION
// ============================================================

const uploadDirectory = path.join(
    __dirname,
    "..",
    "public",
    "prescriptions"
);

// Create prescriptions folder if it doesn't exist
if (!fs.existsSync(uploadDirectory)) {
    fs.mkdirSync(uploadDirectory, {
        recursive: true
    });
}

// ============================================================
// MULTER STORAGE
// ============================================================

const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, uploadDirectory);
    },

    filename: function (req, file, cb) {
        const extension = path.extname(file.originalname);

        const safeName = path
            .basename(file.originalname, extension)
            .replace(/[^a-zA-Z0-9-_]/g, "_")
            .substring(0, 80);

        const filename = `${Date.now()}-${safeName}${extension}`;

        cb(null, filename);
    }
});

// ============================================================
// MULTER UPLOAD
// ============================================================

const upload = multer({
    storage: storage,

    limits: {
        fileSize: 10 * 1024 * 1024
    },

    fileFilter: function (req, file, cb) {
        const allowedExtensions = [
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png"
        ];

        const extension = path
            .extname(file.originalname)
            .toLowerCase();

        if (!allowedExtensions.includes(extension)) {
            return cb(
                new Error(
                    "Only PDF, JPG, JPEG and PNG files are allowed."
                )
            );
        }

        cb(null, true);
    }
});

// ============================================================
// HELPER: DELETE UPLOADED FILE
// ============================================================

function removeUploadedFile(file) {
    if (!file || !file.path) {
        return;
    }

    try {
        if (fs.existsSync(file.path)) {
            fs.unlinkSync(file.path);
        }
    } catch (error) {
        console.error(
            "Could not remove uploaded file:",
            error
        );
    }
}

// ============================================================
// DOCTOR PRESCRIPTION PORTAL
// URL:
// /prescriptions/doctor
// ============================================================

router.get(
    "/doctor",
    (req, res) => {
        res.render(
            "prescription-doctor",
            {
                error: null,
                success: null
            }
        );
    }
);

// ============================================================
// DOCTOR UPLOAD PRESCRIPTION
// URL:
// POST /prescriptions/doctor/upload
// ============================================================

router.post(
    "/doctor/upload",
    upload.single("prescription"),

    async (req, res) => {
        try {

            const email =
                (req.body.email || "")
                    .trim()
                    .toLowerCase();

            const patientEmail =
                (req.body.patient_email || "")
                    .trim()
                    .toLowerCase();

            const description =
                (req.body.description || "")
                    .trim();

            // ----------------------------------------------------
            // VALIDATION
            // ----------------------------------------------------

            if (!email) {
                removeUploadedFile(req.file);

                return res.render(
                    "prescription-doctor",
                    {
                        error:
                            "Please enter your doctor email.",
                        success: null
                    }
                );
            }

            if (!patientEmail) {
                removeUploadedFile(req.file);

                return res.render(
                    "prescription-doctor",
                    {
                        error:
                            "Please enter the patient's email.",
                        success: null
                    }
                );
            }

            if (!req.file) {
                return res.render(
                    "prescription-doctor",
                    {
                        error:
                            "Please select a prescription file.",
                        success: null
                    }
                );
            }

            // ----------------------------------------------------
            // DATABASE
            // ----------------------------------------------------

            const db = mongoose.connection.db;

            const usersCollection =
                db.collection("users");

            const prescriptionsCollection =
                db.collection("prescriptions");

            // ----------------------------------------------------
            // FIND DOCTOR
            // ----------------------------------------------------

            const doctor =
                await usersCollection.findOne({
                    email: email,
                    role: "doctor"
                });

            if (!doctor) {
                removeUploadedFile(req.file);

                return res.render(
                    "prescription-doctor",
                    {
                        error:
                            "No doctor account was found with this email.",
                        success: null
                    }
                );
            }

            // ----------------------------------------------------
            // FIND PATIENT
            // ----------------------------------------------------

            const patient =
                await usersCollection.findOne({
                    email: patientEmail,
                    role: "patient"
                });

            if (!patient) {
                removeUploadedFile(req.file);

                return res.render(
                    "prescription-doctor",
                    {
                        error:
                            "No patient account was found with this email.",
                        success: null
                    }
                );
            }

            // ----------------------------------------------------
            // SAVE PRESCRIPTION
            // ----------------------------------------------------

            const prescription = {

                doctor_id: doctor._id,

                doctor_name:
                    doctor.name || "",

                doctor_email:
                    doctor.email || "",

                patient_id: patient._id,

                patient_name:
                    patient.name || "",

                patient_email:
                    patient.email || "",

                original_filename:
                    req.file.originalname,

                stored_filename:
                    req.file.filename,

                file_path:
                    `/prescriptions/${req.file.filename}`,

                description:
                    description,

                uploaded_at:
                    new Date()
            };

            await prescriptionsCollection.insertOne(
                prescription
            );

            // ----------------------------------------------------
            // SUCCESS
            // ----------------------------------------------------

            return res.render(
                "prescription-doctor",
                {
                    error: null,

                    success:
                        `Prescription uploaded successfully for ${patient.name}.`
                }
            );

        } catch (error) {

            console.error(
                "Prescription upload error:",
                error
            );

            removeUploadedFile(req.file);

            return res.status(500).render(
                "prescription-doctor",
                {
                    error:
                        "Unable to upload prescription.",
                    success: null
                }
            );
        }
    }
);

// ============================================================
// PATIENT PRESCRIPTION PORTAL
// URL:
// /prescriptions/patient
// ============================================================

router.get(
    "/patient",
    (req, res) => {

        res.render(
            "prescription-patient",
            {
                error: null,
                patient: null,
                prescriptions: null
            }
        );

    }
);

// ============================================================
// PATIENT ACCESS PRESCRIPTIONS
// URL:
// POST /prescriptions/patient
// ============================================================

router.post(
    "/patient",

    async (req, res) => {

        try {

            const email =
                (req.body.email || "")
                    .trim()
                    .toLowerCase();

            const password =
                (req.body.password || "")
                    .trim();

            // ----------------------------------------------------
            // VALIDATION
            // ----------------------------------------------------

            if (!email || !password) {

                return res.render(
                    "prescription-patient",
                    {
                        error:
                            "Please enter your email and password.",

                        patient: null,

                        prescriptions: null
                    }
                );

            }

            // ----------------------------------------------------
            // DATABASE
            // ----------------------------------------------------

            const db = mongoose.connection.db;

            const usersCollection =
                db.collection("users");

            const prescriptionsCollection =
                db.collection("prescriptions");

            // ----------------------------------------------------
            // FIND PATIENT
            // ----------------------------------------------------

            const patient =
                await usersCollection.findOne({
                    email: email,
                    role: "patient"
                });

            if (!patient) {

                return res.render(
                    "prescription-patient",
                    {
                        error:
                            "Invalid email or password.",

                        patient: null,

                        prescriptions: null
                    }
                );

            }

            // ----------------------------------------------------
            // GET STORED PASSWORD
            // ----------------------------------------------------

            const storedPassword =
                patient.password ||
                patient.passwordHash ||
                patient.password_hash;

            if (!storedPassword) {

                return res.render(
                    "prescription-patient",
                    {
                        error:
                            "This patient account does not have a usable password.",

                        patient: null,

                        prescriptions: null
                    }
                );

            }

            // ----------------------------------------------------
            // CHECK PASSWORD
            // ----------------------------------------------------

            const passwordMatches =
                await bcrypt.compare(
                    password,
                    storedPassword
                );

            if (!passwordMatches) {

                return res.render(
                    "prescription-patient",
                    {
                        error:
                            "Invalid email or password.",

                        patient: null,

                        prescriptions: null
                    }
                );

            }

            // ----------------------------------------------------
            // GET PRESCRIPTIONS
            // ----------------------------------------------------

            const prescriptions =
                await prescriptionsCollection
                    .find({
                        patient_id: patient._id
                    })
                    .sort({
                        uploaded_at: -1
                    })
                    .toArray();

            // ----------------------------------------------------
            // RENDER
            // ----------------------------------------------------

            return res.render(
                "prescription-patient",
                {
                    error: null,

                    patient: {
                        name:
                            patient.name || "",

                        email:
                            patient.email || ""
                    },

                    prescriptions:
                        prescriptions
                }
            );

        } catch (error) {

            console.error(
                "Patient prescription error:",
                error
            );

            return res.status(500).render(
                "prescription-patient",
                {
                    error:
                        "Unable to retrieve prescriptions.",

                    patient: null,

                    prescriptions: null
                }
            );
        }
    }
);

// ============================================================
// DOWNLOAD PRESCRIPTION
// URL:
// /prescriptions/download/:filename
// ============================================================

router.get(
    "/download/:filename",

    (req, res) => {

        try {

            const filename =
                path.basename(
                    req.params.filename
                );

            const filePath =
                path.join(
                    uploadDirectory,
                    filename
                );

            // ----------------------------------------------------
            // CHECK FILE
            // ----------------------------------------------------

            if (!fs.existsSync(filePath)) {

                return res
                    .status(404)
                    .send(
                        "Prescription file not found."
                    );

            }

            // ----------------------------------------------------
            // DOWNLOAD
            // ----------------------------------------------------

            return res.download(
                filePath
            );

        } catch (error) {

            console.error(
                "Prescription download error:",
                error
            );

            return res
                .status(500)
                .send(
                    "Unable to download prescription."
                );
        }
    }
);

// ============================================================
// EXPORT ROUTER
// ============================================================

module.exports = router;