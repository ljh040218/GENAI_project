const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const pool = require("./config/database");
const productRoutes = require('./routes/products');

// 라우트 require
const authRoutes = require("./routes/auth");
const beautyProfileRoutes = require("./routes/beautyProfile");

dotenv.config();
const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use('/api/products', productRoutes);

app.use(
  cors({
    origin: process.env.CORS_ORIGIN || "*",
    credentials: true,
  })
);

// PostgreSQL 연결
pool
  .connect()
  .then(() => console.log("Connected to PostgreSQL via Railway"))
  .catch((err) => console.error("PostgreSQL connection error:", err));

app.get("/api/health", (req, res) => {
  res.json({
    success: true,
    message: "Server is running",
    timestamp: new Date(),
  });
});

// 라우트 등록
app.use("/api/auth", authRoutes);
app.use("/api/profile", beautyProfileRoutes);

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
  console.log(`Environment: ${process.env.RAILWAY_ENVIRONMENT || "local"}`);
});

module.exports = app;
