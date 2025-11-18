const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const pool = require("./config/database");
const productRoutes = require('./routes/products');

// 라우트 require
const authRoutes = require("./routes/auth");
const beautyProfileRoutes = require("./routes/beautyProfile");
const imageAnalysisRoutes = require('./routes/imageAnalysis');

dotenv.config();
const app = express();

// CORS 설정을 가장 먼저
app.use(
  cors({
    origin: process.env.CORS_ORIGIN || "*",
    credentials: true,
  })
);

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get("/", (req, res) => {
  res.json({
    success: true,
    message: "Beauty AI Backend Server",
    status: "running",
    timestamp: new Date().toISOString(),
    environment: process.env.RAILWAY_ENVIRONMENT || "local"
  });
});

app.get("/api/health", (req, res) => {
  res.json({
    success: true,
    message: "Server is running",
    timestamp: new Date(),
  });
});

// 메모리 모니터링 엔드포인트
app.get("/memory", (req, res) => {
  const usage = process.memoryUsage();
  const formatMB = (bytes) => Math.round(bytes / 1024 / 1024);
  
  res.json({
    rss: `${formatMB(usage.rss)} MB`,
    heapTotal: `${formatMB(usage.heapTotal)} MB`,
    heapUsed: `${formatMB(usage.heapUsed)} MB`,
    external: `${formatMB(usage.external)} MB`,
    limit: "512 MB",
    usage_percent: `${Math.round(usage.rss / (512 * 1024 * 1024) * 100)}%`
  });
});

// 라우트 설정
app.use('/api/products', productRoutes);
app.use('/api/image', imageAnalysisRoutes);
app.use("/api/auth", authRoutes);
app.use("/api/profile", beautyProfileRoutes);

// PostgreSQL 연결
pool
  .connect()
  .then(() => console.log("Connected to PostgreSQL via Railway"))
  .catch((err) => console.error("PostgreSQL connection error:", err));

process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  process.exit(0);
});

const PORT = process.env.PORT || 8080;

const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server is running on port ${PORT}`);
  console.log(`Environment: ${process.env.RAILWAY_ENVIRONMENT || "local"}`);
  console.log(`Health check: http://localhost:${PORT}/`);
});

module.exports = app;