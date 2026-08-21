# FloatChat project scaffold

# Root files
$rootFiles = @("README.md", ".env.example", ".gitignore", "docker-compose.yml", "requirements.txt", "LICENSE")
foreach ($f in $rootFiles) { New-Item -ItemType File -Force $f | Out-Null }

# Directories
$dirs = @(
  "backend/models",
  "backend/etl",
  "backend/vectorstore/schema_docs",
  "backend/nl2sql",
  "backend/services",
  "backend/api",
  "backend/ml",
  "backend/utils",
  "backend/tests",
  "frontend/src/i18n/locales",
  "frontend/src/api",
  "frontend/src/context",
  "frontend/src/hooks",
  "frontend/src/components",
  "frontend/src/pages",
  "data/raw",
  "data/processed",
  "data/schema_docs",
  "notebooks",
  "scripts",
  "docs"
)
foreach ($d in $dirs) { New-Item -ItemType Directory -Force $d | Out-Null }

# All files to create
$files = @(
  # backend core
  "backend/main.py",
  "backend/config.py",
  "backend/database.py",
  # models
  "backend/models/__init__.py",
  "backend/models/float_metadata.py",
  "backend/models/profile.py",
  "backend/models/trajectory.py",
  "backend/models/bgc_profile.py",
  # etl
  "backend/etl/__init__.py",
  "backend/etl/fetch_argo.py",
  "backend/etl/parse_netcdf.py",
  "backend/etl/qc_filter.py",
  "backend/etl/load_to_db.py",
  "backend/etl/scheduler.py",
  # vectorstore
  "backend/vectorstore/__init__.py",
  "backend/vectorstore/embed_metadata.py",
  "backend/vectorstore/chroma_client.py",
  # nl2sql
  "backend/nl2sql/__init__.py",
  "backend/nl2sql/prompt_templates.py",
  "backend/nl2sql/query_generator.py",
  "backend/nl2sql/sql_validator.py",
  "backend/nl2sql/template_queries.py",
  "backend/nl2sql/router.py",
  # services
  "backend/services/__init__.py",
  "backend/services/chat_service.py",
  "backend/services/query_service.py",
  "backend/services/viz_service.py",
  "backend/services/anomaly_service.py",
  "backend/services/translation_service.py",
  "backend/services/trajectory_predictor.py",
  "backend/services/voice_service.py",
  "backend/services/explainability_service.py",
  "backend/services/mode_service.py",
  "backend/services/bgc_service.py",
  # api
  "backend/api/__init__.py",
  "backend/api/chat.py",
  "backend/api/query.py",
  "backend/api/floats.py",
  "backend/api/viz.py",
  "backend/api/voice.py",
  "backend/api/export.py",
  "backend/api/health.py",
  # ml
  "backend/ml/__init__.py",
  "backend/ml/trajectory_model.py",
  "backend/ml/train_trajectory.py",
  "backend/ml/anomaly_detection.py",
  # utils
  "backend/utils/__init__.py",
  "backend/utils/geo_utils.py",
  "backend/utils/cache.py",
  "backend/utils/logger.py",
  # tests
  "backend/tests/test_etl.py",
  "backend/tests/test_nl2sql.py",
  "backend/tests/test_validator.py",
  "backend/tests/test_api.py",
  # frontend
  "frontend/package.json",
  "frontend/vite.config.js",
  "frontend/src/main.jsx",
  "frontend/src/App.jsx",
  "frontend/src/i18n/index.js",
  "frontend/src/i18n/locales/en.json",
  "frontend/src/i18n/locales/hi.json",
  "frontend/src/i18n/locales/ta.json",
  "frontend/src/i18n/locales/bn.json",
  "frontend/src/api/client.js",
  "frontend/src/context/ChatContext.jsx",
  "frontend/src/hooks/useChat.js",
  "frontend/src/hooks/useVoice.js",
  "frontend/src/components/ChatPanel.jsx",
  "frontend/src/components/MessageBubble.jsx",
  "frontend/src/components/VoiceInput.jsx",
  "frontend/src/components/MapView.jsx",
  "frontend/src/components/DepthProfileChart.jsx",
  "frontend/src/components/TimeSeriesChart.jsx",
  "frontend/src/components/TrajectoryPredictionLayer.jsx",
  "frontend/src/components/AnomalyBanner.jsx",
  "frontend/src/components/ExplainabilityPanel.jsx",
  "frontend/src/components/ModeToggle.jsx",
  "frontend/src/components/ExportButton.jsx",
  "frontend/src/pages/Home.jsx",
  "frontend/src/pages/Dashboard.jsx",
  "frontend/src/pages/About.jsx",
  # notebooks / scripts / docs
  "notebooks/exploration.ipynb",
  "scripts/init_db.sql",
  "scripts/seed_demo_data.py",
  "scripts/run_pipeline.sh",
  "docs/architecture.md",
  "docs/db_schema.md",
  "docs/demo_script.md"
)

foreach ($f in $files) { New-Item -ItemType File -Force $f | Out-Null }

Write-Host "FloatChat structure created successfully!" -ForegroundColor Green
