# Code Graph - monarch

> Auto-generated map. 158 files, 122 import links, 80 clusters. Regenerate after structural changes.

## Clusters

| # | Cluster | Files | What it is |
|---|---|---|---|
| 1 | **Content Inference API** | 22 | FastAPI app scores content via TRIBE v2 model, computes NAA + opinion dynamics, generates PDF audit reports. |
| 2 | **3D Brain Renderer** | 18 | Three.js-powered visualization system that renders fMRI activation onto high-resolution cortical surfaces with synchronized animation and interactive controls. |
| 3 | **TRIBE Neuroscience Engine** | 15 | Experiment framework for training neural encoding models on fMRI datasets across multiple neuroimaging studies (Algonauts, BOLD, language stimuli). |
| 4 | **Chart Components** | 10 | ECharts-based visualization components sharing a common theme and SSR-safe wrapper for rendering diverse chart types (scatter, bars, gauges, force graphs, metrics). |
| 5 | **Scan State Engine** | 7 | Manages scan results, brain ROI activation state, and audience-specific interpretation of NAA metrics for visualization. |
| 6 | **Brain Visualization** | 6 | Plotting module for cortical and subcortical brain regions using matplotlib, nilearn, and pyvista backends. |
| 7 | **Inference API Core** | 5 | FastAPI inference server infrastructure with API key authentication, rate limiting, and TRIBE v2 model lifecycle management. |
| 8 | **Authenticated Scans** | 3 | Scan operations enforced with user ownership verification and rate limiting across mutations. |
| 9 | **Authentication Middleware** | 1 | Clerk middleware protecting scanner, report, and batch routes with authentication. |
| 10 | **Next.js TypeScript Config** | 1 | Auto-generated type definitions for Next.js image and environment APIs. |
| 11 | **Next.js Frontend Config** | 1 | Web application configuration with production optimizations and security headers for Docker deployment. |
| 12 | **CSS Styling Config** | 1 | PostCSS configuration that processes Tailwind CSS for the web application. |
| 13 | **Tailwind Config** | 1 | Configures Tailwind CSS content paths and theme variables for the Next.js web app. |
| 14 | **Convex User Schema** | 1 | Defines the database schema for user accounts with tier-based credit management and Clerk authentication integration. |
| 15 | **User Credits Query** | 1 | Convex query that retrieves remaining and maximum credits for a user by Clerk ID, defaulting to zero if user not found. |
| 16 | **Root Layout & Providers** | 1 | Next.js app shell setting up Clerk auth, Convex backend, scan provider, and global styles with header component. |
| 17 | **Landing Page Hero** | 1 | Next.js client component rendering home page with Phosphor icon imports for feature showcase. |
| 18 | **Batch UI Layout** | 1 | Layout wrapper for batch operations using split-panel view structure. |
| 19 | **Batch Audit Page** | 1 | Standalone /batch route rendering batch audit panel with item selection and detailed report view. |
| 20 | **Report Layout** | 1 | Next.js layout wrapper that applies split-pane structure to report views. |
| 21 | **Report Dashboard** | 1 | Main report page composing multiple audit and financial visualization charts. |
| 22 | **Audit Comparison Layout** | 1 | Layout wrapper for split-view scanner interface with side-by-side comparison capabilities. |
| 23 | **Scanner Dashboard** | 1 | Multi-tab interface for content auditing with batch processing, comparison, and multimodal analysis modes. |
| 24 | **Clerk Auth SignIn** | 1 | Sign-in page component using Clerk authentication with email input and session management. |
| 25 | **Clerk Sign-Up Page** | 1 | Client-side sign-up page using Clerk authentication with email state management and Next.js routing. |
| 26 | **Audit Report Display** | 1 | Client component rendering audit narratives with summary, findings, and caveats sections. |
| 27 | **Math Equation Renderer** | 1 | React component for rendering LaTeX equations using KaTeX with inline/block display modes. |
| 28 | **Header Navigation** | 1 | Client-side header component with Clerk authentication UI that conditionally renders sign-in or user profile button. |
| 29 | **Icon Components** | 1 | Reusable SVG icon components with configurable size and styling for web UI. |
| 30 | **Brain Split Layout** | 1 | Layout component splitting brain visualization panel from scan result controls, supporting comparison mode. |
| 31 | **Tab Navigation** | 1 | React tab navigation component with TypeScript interfaces for managing tab state and onChange callbacks. |
| 32 | **Brain Depth Shading** | 1 | Computes per-face grey palette from sulcal depth to render 3D brain surface with uniform polygonal shading. |
| 33 | **Guide Toggle Button** | 1 | Reusable button component for toggling guide visibility in the BrainViewer interface. |
| 34 | **NAA Classification Explainer** | 1 | Explainer component that displays NAA classification levels (LOW/MOD/HIGH) with associated affinity and deletion metrics. |
| 35 | **Report Summary Display** | 1 | Renders executive summary paragraph from scan results on report page. |
| 36 | **Scientific Disclaimers** | 1 | Footer component displaying methodology disclaimers for neuroscience result views. |
| 37 | **Demographic Selector** | 1 | UI component for selecting demographic categories in scanner with dropdown interaction. |
| 38 | **Scan Result Display** | 1 | React component props for rendering scan results with audience-specific takeaways and loading state. |
| 39 | **Batch Scanning** | 1 | Component for uploading and visualizing batch text analysis results in a scatter chart. |
| 40 | **Scan Comparison UI** | 1 | Tab component for displaying and comparing scan results with demographic charts and element cards. |
| 41 | **Multimodal Analysis UI** | 1 | React component for visualizing multimodal brain activation data with ROI processing and synthetic scan support. |
| 42 | **Scanner Dashboard UI** | 1 | Tabbed scanning interface with scientific charts, gauges, and analysis visualizations. |
| 43 | **Brain Hemisphere Coordinates** | 1 | Utilities for loading fsaverage5 pial surface vertex positions and generating spatially coherent brain activation data. |
| 44 | **Convex Provider** | 1 | Client provider setup combining Convex backend client with Clerk authentication, guards against missing deployment URL. |
| 45 | **Multimodal Encoder Integration** | 1 | Interprets per-modality neural activity from TRIBE v2 encoders (text/audio/video) mapped to cortical networks. |
| 46 | **NAA Classification Format** | 1 | Defines classification types (LOW/MOD/HIGH) and human-readable labels (Neutral/Mixed/Reactive) for assessment scoring shared between scanner and reports. |
| 47 | **Data Normalization** | 1 | Percentile-based robust normalization utility for rescaling visualization data to [0,1] range. |
| 48 | **Brain Region Labels** | 1 | Manages metadata and descriptions for 17 brain regions in the Show Guide overlay, organized by neural system types (affective, deliberative, sensory, social). |
| 49 | **Input Sanitization** | 1 | Utilities for stripping HTML and preventing XSS attacks in user-provided scan text. |
| 50 | **Platform Detection** | 1 | Identifies media platforms (YouTube, TikTok, Instagram, Spotify, etc.) from URLs for client-side categorization. |
| 51 | **Inference Security** | 1 | Security middleware for the inference server request pipeline. |
| 52 | **Request/Response Models** | 1 | Pydantic models and enums defining schema for inference service API requests and responses. |
| 53 | **Report Chart Rendering** | 1 | Matplotlib chart renderers that generate PNG bytes for PDF report embedding with unified monochrome-plus-fire styling. |
| 54 | **Resumable Batch Inference** | 1 | Checkpoints batch inference progress using memory-mapped arrays and JSON tracking to resume from failures without reprocessing completed items. |
| 55 | **Multimodal Preprocessing** | 1 | Thin wrapper layer enforcing limits and extracting formats (language, timestamps, frames) from text, audio, and video inputs for TRIBE v2 processing pipeline. |
| 56 | **Inference Utilities** | 1 | Lower-level helpers for preprocessing, file handling, and batch checkpointing in the inference service. |
| 57 | **ROI Index Caching** | 1 | Pre-computes HCP MMP1.0 ROI vertex-index cache to enable fast API server lookups without tribev2 import overhead. |
| 58 | **Ising Alpha Calibration** | 1 | Estimates opinion-dynamics coupling parameter from neural arousal asymmetry via empirical regression. |
| 59 | **ROI Vertex Export** | 1 | Exports HCP brain region-of-interest vertex indices from fsaverage5 mesh to backend cache and frontend visualization. |
| 60 | **Brain Surface Masking** | 1 | Generates and geometrically validates medial-wall masks for fsaverage5 brain surfaces from FreeSurfer data. |
| 61 | **Brain Surface Upsampling** | 1 | Creates lookup maps for expanding low-resolution brain surface data onto high-resolution meshes using nearest-neighbor geometry. |
| 62 | **Model Weight Prewarming** | 1 | Script pre-downloads ML model weights (gTTS, WhisperX, LLaMA, Wav2Vec-BERT) to mounted cache before inference serving to eliminate request-time download latency. |
| 63 | **Inference Deployment Validation** | 1 | Smoke test that verifies deployment environment health for TRIBE v2 inference by checking Python/GPU/model dependencies and running a single prediction round-trip. |
| 64 | **Inference Test Fixtures** | 1 | Pytest configuration providing shared test fixtures for inference tests, including ROI cache mocking to avoid tribev2 dependency. |
| 65 | **FastAPI Boot Tests** | 1 | Smoke test verifying app startup and health endpoint work with model loading disabled. |
| 66 | **Auth Middleware Tests** | 1 | Tests for APIKeyMiddleware authenticating requests via API keys in the inference service. |
| 67 | **Blob Storage & Serialization** | 1 | Tests in-memory blob storage and numpy array serialization/deserialization for inference services. |
| 68 | **Inference Service Tests** | 1 | Unit tests for TribeInferenceService covering structural paths; GPU model load/predict tested via deployment smoke test. |
| 69 | **Landau Magnetic Analysis** | 1 | Test suite for Landau theory phase-transition calculations—equilibrium magnetization, susceptibility curves, physics math independent of external services. |
| 70 | **NAA Inference Testing** | 1 | Unit tests for neural analysis computation using cached ROI data fixtures. |
| 71 | **Inference Pooling Tests** | 1 | Unit tests for aggregation functions (mean, peak, trimmed-mean pooling) on prediction tensors in the inference service. |
| 72 | **Rate Limit Middleware** | 1 | Token-bucket rate limiting middleware tests for FastAPI services with configurable refill rates and proxy trust. |
| 73 | **Report Testing** | 1 | Offline unit and integration tests for the audit-report API endpoint, context builder, and message rendering pipeline. |
| 74 | **ROI Inference Tests** | 1 | Tests disk-cache fallback path for ROI service inference, with integration tests for live tribev2 lookup skipped if dependencies unavailable. |
| 75 | **Timeseries Playback Tests** | 1 | Tests timeseries endpoint playback by injecting frames directly without model dependency. |
| 76 | **Inference Tests** | 1 | Test suite package initialization for inference service. |
| 77 | **Brain Mesh Export** | 1 | Converts fsaverage5 brain surfaces to Three.js-compatible formats (JSON, BIN, GLB) for neuroimaging visualization. |
| 78 | **TRIBE v2 Demo Utils** | 1 | Utilities for TribeModel inference demonstrations and event DataFrame construction. |
| 79 | **TRIBE Model Export** | 1 | Exposes TribeModel from tribev2 inference service as package entry point. |
| 80 | **TRIBE Experiment Grids** | 1 | Grid configurations and defaults for TRIBE v2 neuroscience experiments. |

### 1. Content Inference API
_FastAPI app scores content via TRIBE v2 model, computes NAA + opinion dynamics, generates PDF audit reports._

- `services\inference\app\config.py`
- `services\inference\app\dependencies.py`
- `services\inference\app\middleware\input_validation.py`
- `services\inference\app\models\enums.py`
- `services\inference\app\models\schemas.py`
- `services\inference\app\routers\batch.py`
- `services\inference\app\routers\compare.py`
- `services\inference\app\routers\report.py`
- `services\inference\app\routers\scan.py`
- `services\inference\app\services\__init__.py`
- `services\inference\app\services\alpha_calibration.py`
- `services\inference\app\services\blob_store.py`
- `services\inference\app\services\gemma_report.py`
- `services\inference\app\services\inference.py`
- `services\inference\app\services\landau.py`
- `services\inference\app\services\naa.py`
- `services\inference\app\services\pooling.py`
- `services\inference\app\services\report_generator.py`
- `services\inference\app\services\roi.py`
- `services\inference\app\services\stores.py`
- `services\inference\app\services\susceptibility.py`
- `services\inference\app\utils\file_handling.py`

### 2. 3D Brain Renderer
_Three.js-powered visualization system that renders fMRI activation onto high-resolution cortical surfaces with synchronized animation and interactive controls._

- `apps\web\src\components\BrainViewer\engine\ActivationMapper.ts`
- `apps\web\src\components\BrainViewer\engine\AnimationController.ts`
- `apps\web\src\components\BrainViewer\engine\BrainEngine.ts`
- `apps\web\src\components\BrainViewer\engine\CameraPresets.ts`
- `apps\web\src\components\BrainViewer\engine\Colormap.ts`
- `apps\web\src\components\BrainViewer\engine\HeadShell.ts`
- `apps\web\src\components\BrainViewer\engine\HemisphereManager.ts`
- `apps\web\src\components\BrainViewer\engine\InflateManager.ts`
- `apps\web\src\components\BrainViewer\engine\MeshLoader.ts`
- `apps\web\src\components\BrainViewer\engine\ROILabelManager.ts`
- `apps\web\src\components\BrainViewer\index.tsx`
- `apps\web\src\components\BrainViewer\types.ts`
- `apps\web\src\components\BrainViewer\ui\ActivityLegend.tsx`
- `apps\web\src\components\BrainViewer\ui\BrainControls.tsx`
- `apps\web\src\components\BrainViewer\ui\ControlToggles.tsx`
- `apps\web\src\components\BrainViewer\ui\MultimodalLegend.tsx`
- `apps\web\src\components\BrainViewer\ui\PlaybackControls.tsx`
- `apps\web\src\components\BrainViewer\ui\ROIDescriptionPanel.tsx`

### 3. TRIBE Neuroscience Engine
_Experiment framework for training neural encoding models on fMRI datasets across multiple neuroimaging studies (Algonauts, BOLD, language stimuli)._

- `services\inference\tribev2\tribev2\eventstransforms.py`
- `services\inference\tribev2\tribev2\grids\defaults.py`
- `services\inference\tribev2\tribev2\grids\run_cortical.py`
- `services\inference\tribev2\tribev2\grids\run_subcortical.py`
- `services\inference\tribev2\tribev2\grids\test_run.py`
- `services\inference\tribev2\tribev2\main.py`
- `services\inference\tribev2\tribev2\model.py`
- `services\inference\tribev2\tribev2\pl_module.py`
- `services\inference\tribev2\tribev2\studies\__init__.py`
- `services\inference\tribev2\tribev2\studies\algonauts2025.py`
- `services\inference\tribev2\tribev2\studies\lahner2024bold.py`
- `services\inference\tribev2\tribev2\studies\lebel2023bold.py`
- `services\inference\tribev2\tribev2\studies\wen2017.py`
- `services\inference\tribev2\tribev2\utils.py`
- `services\inference\tribev2\tribev2\utils_fmri.py`

### 4. Chart Components
_ECharts-based visualization components sharing a common theme and SSR-safe wrapper for rendering diverse chart types (scatter, bars, gauges, force graphs, metrics)._

- `apps\web\src\components\charts\BatchScatter.tsx`
- `apps\web\src\components\charts\EchartsBase.tsx`
- `apps\web\src\components\charts\LandauCurve.tsx`
- `apps\web\src\components\charts\MultimodalBars.tsx`
- `apps\web\src\components\charts\NAADistributionMini.tsx`
- `apps\web\src\components\charts\NAAGauge.tsx`
- `apps\web\src\components\charts\NeuralForceGraph.tsx`
- `apps\web\src\components\charts\ROIBreakdown.tsx`
- `apps\web\src\components\charts\SusceptibilityChart.tsx`
- `apps\web\src\components\charts\echarts-theme.ts`

### 5. Scan State Engine
_Manages scan results, brain ROI activation state, and audience-specific interpretation of NAA metrics for visualization._

- `apps\web\src\lib\demographics.ts`
- `apps\web\src\lib\example-content.ts`
- `apps\web\src\lib\inference-client.ts`
- `apps\web\src\lib\mock-data.ts`
- `apps\web\src\lib\roi-activation.ts`
- `apps\web\src\lib\scan-provider.tsx`
- `apps\web\src\lib\scan-store.ts`

### 6. Brain Visualization
_Plotting module for cortical and subcortical brain regions using matplotlib, nilearn, and pyvista backends._

- `services\inference\tribev2\tribev2\plotting\__init__.py`
- `services\inference\tribev2\tribev2\plotting\base.py`
- `services\inference\tribev2\tribev2\plotting\cortical.py`
- `services\inference\tribev2\tribev2\plotting\cortical_pv.py`
- `services\inference\tribev2\tribev2\plotting\subcortical.py`
- `services\inference\tribev2\tribev2\plotting\utils.py`

### 7. Inference API Core
_FastAPI inference server infrastructure with API key authentication, rate limiting, and TRIBE v2 model lifecycle management._

- `services\inference\app\__init__.py`
- `services\inference\app\main.py`
- `services\inference\app\middleware\api_key.py`
- `services\inference\app\middleware\rate_limit.py`
- `services\inference\app\routers\__init__.py`

### 8. Authenticated Scans
_Scan operations enforced with user ownership verification and rate limiting across mutations._

- `apps\web\convex\lib\auth.ts`
- `apps\web\convex\lib\rateLimit.ts`
- `apps\web\convex\scans.ts`

### 9. Authentication Middleware
_Clerk middleware protecting scanner, report, and batch routes with authentication._

- `apps\web\middleware.ts`

### 10. Next.js TypeScript Config
_Auto-generated type definitions for Next.js image and environment APIs._

- `apps\web\next-env.d.ts`

### 11. Next.js Frontend Config
_Web application configuration with production optimizations and security headers for Docker deployment._

- `apps\web\next.config.mjs`

### 12. CSS Styling Config
_PostCSS configuration that processes Tailwind CSS for the web application._

- `apps\web\postcss.config.mjs`

### 13. Tailwind Config
_Configures Tailwind CSS content paths and theme variables for the Next.js web app._

- `apps\web\tailwind.config.ts`

### 14. Convex User Schema
_Defines the database schema for user accounts with tier-based credit management and Clerk authentication integration._

- `apps\web\convex\schema.ts`

### 15. User Credits Query
_Convex query that retrieves remaining and maximum credits for a user by Clerk ID, defaulting to zero if user not found._

- `apps\web\convex\users.ts`

### 16. Root Layout & Providers
_Next.js app shell setting up Clerk auth, Convex backend, scan provider, and global styles with header component._

- `apps\web\src\app\layout.tsx`

### 17. Landing Page Hero
_Next.js client component rendering home page with Phosphor icon imports for feature showcase._

- `apps\web\src\app\page.tsx`

### 18. Batch UI Layout
_Layout wrapper for batch operations using split-panel view structure._

- `apps\web\src\app\batch\layout.tsx`

### 19. Batch Audit Page
_Standalone /batch route rendering batch audit panel with item selection and detailed report view._

- `apps\web\src\app\batch\page.tsx`

### 20. Report Layout
_Next.js layout wrapper that applies split-pane structure to report views._

- `apps\web\src\app\report\layout.tsx`

### 21. Report Dashboard
_Main report page composing multiple audit and financial visualization charts._

- `apps\web\src\app\report\page.tsx`

### 22. Audit Comparison Layout
_Layout wrapper for split-view scanner interface with side-by-side comparison capabilities._

- `apps\web\src\app\scanner\layout.tsx`

### 23. Scanner Dashboard
_Multi-tab interface for content auditing with batch processing, comparison, and multimodal analysis modes._

- `apps\web\src\app\scanner\page.tsx`

### 24. Clerk Auth SignIn
_Sign-in page component using Clerk authentication with email input and session management._

- `apps\web\src\app\sign-in\[[...sign-in]]\page.tsx`

### 25. Clerk Sign-Up Page
_Client-side sign-up page using Clerk authentication with email state management and Next.js routing._

- `apps\web\src\app\sign-up\[[...sign-up]]\page.tsx`

### 26. Audit Report Display
_Client component rendering audit narratives with summary, findings, and caveats sections._

- `apps\web\src\components\AuditReportCard.tsx`

### 27. Math Equation Renderer
_React component for rendering LaTeX equations using KaTeX with inline/block display modes._

- `apps\web\src\components\Equation.tsx`

### 28. Header Navigation
_Client-side header component with Clerk authentication UI that conditionally renders sign-in or user profile button._

- `apps\web\src\components\Header.tsx`

### 29. Icon Components
_Reusable SVG icon components with configurable size and styling for web UI._

- `apps\web\src\components\icons.tsx`

### 30. Brain Split Layout
_Layout component splitting brain visualization panel from scan result controls, supporting comparison mode._

- `apps\web\src\components\SplitLayout.tsx`

### 31. Tab Navigation
_React tab navigation component with TypeScript interfaces for managing tab state and onChange callbacks._

- `apps\web\src\components\TabNav.tsx`

### 32. Brain Depth Shading
_Computes per-face grey palette from sulcal depth to render 3D brain surface with uniform polygonal shading._

- `apps\web\src\components\BrainViewer\engine\SulcalShading.ts`

### 33. Guide Toggle Button
_Reusable button component for toggling guide visibility in the BrainViewer interface._

- `apps\web\src\components\BrainViewer\ui\GuideButton.tsx`

### 34. NAA Classification Explainer
_Explainer component that displays NAA classification levels (LOW/MOD/HIGH) with associated affinity and deletion metrics._

- `apps\web\src\components\explainers\NAAExplainer.tsx`

### 35. Report Summary Display
_Renders executive summary paragraph from scan results on report page._

- `apps\web\src\components\explainers\ReportSummary.tsx`

### 36. Scientific Disclaimers
_Footer component displaying methodology disclaimers for neuroscience result views._

- `apps\web\src\components\explainers\ScientificDisclaimer.tsx`

### 37. Demographic Selector
_UI component for selecting demographic categories in scanner with dropdown interaction._

- `apps\web\src\components\scanner\DemographicSelect.tsx`

### 38. Scan Result Display
_React component props for rendering scan results with audience-specific takeaways and loading state._

- `apps\web\src\components\scanner\ElementCard.tsx`

### 39. Batch Scanning
_Component for uploading and visualizing batch text analysis results in a scatter chart._

- `apps\web\src\components\scanner-tabs\BatchTab.tsx`

### 40. Scan Comparison UI
_Tab component for displaying and comparing scan results with demographic charts and element cards._

- `apps\web\src\components\scanner-tabs\CompareTab.tsx`

### 41. Multimodal Analysis UI
_React component for visualizing multimodal brain activation data with ROI processing and synthetic scan support._

- `apps\web\src\components\scanner-tabs\MultimodalTab.tsx`

### 42. Scanner Dashboard UI
_Tabbed scanning interface with scientific charts, gauges, and analysis visualizations._

- `apps\web\src\components\scanner-tabs\ScanTab.tsx`

### 43. Brain Hemisphere Coordinates
_Utilities for loading fsaverage5 pial surface vertex positions and generating spatially coherent brain activation data._

- `apps\web\src\lib\brain-data.ts`

### 44. Convex Provider
_Client provider setup combining Convex backend client with Clerk authentication, guards against missing deployment URL._

- `apps\web\src\lib\convex-provider.tsx`

### 45. Multimodal Encoder Integration
_Interprets per-modality neural activity from TRIBE v2 encoders (text/audio/video) mapped to cortical networks._

- `apps\web\src\lib\multimodal.ts`

### 46. NAA Classification Format
_Defines classification types (LOW/MOD/HIGH) and human-readable labels (Neutral/Mixed/Reactive) for assessment scoring shared between scanner and reports._

- `apps\web\src\lib\naa-format.ts`

### 47. Data Normalization
_Percentile-based robust normalization utility for rescaling visualization data to [0,1] range._

- `apps\web\src\lib\normalize.ts`

### 48. Brain Region Labels
_Manages metadata and descriptions for 17 brain regions in the Show Guide overlay, organized by neural system types (affective, deliberative, sensory, social)._

- `apps\web\src\lib\roi-labels.ts`

### 49. Input Sanitization
_Utilities for stripping HTML and preventing XSS attacks in user-provided scan text._

- `apps\web\src\lib\sanitize.ts`

### 50. Platform Detection
_Identifies media platforms (YouTube, TikTok, Instagram, Spotify, etc.) from URLs for client-side categorization._

- `apps\web\src\lib\url-detector.ts`

### 51. Inference Security
_Security middleware for the inference server request pipeline._

- `services\inference\app\middleware\__init__.py`

### 52. Request/Response Models
_Pydantic models and enums defining schema for inference service API requests and responses._

- `services\inference\app\models\__init__.py`

### 53. Report Chart Rendering
_Matplotlib chart renderers that generate PNG bytes for PDF report embedding with unified monochrome-plus-fire styling._

- `services\inference\app\services\report_charts.py`

### 54. Resumable Batch Inference
_Checkpoints batch inference progress using memory-mapped arrays and JSON tracking to resume from failures without reprocessing completed items._

- `services\inference\app\utils\checkpoint.py`

### 55. Multimodal Preprocessing
_Thin wrapper layer enforcing limits and extracting formats (language, timestamps, frames) from text, audio, and video inputs for TRIBE v2 processing pipeline._

- `services\inference\app\utils\preprocessing.py`

### 56. Inference Utilities
_Lower-level helpers for preprocessing, file handling, and batch checkpointing in the inference service._

- `services\inference\app\utils\__init__.py`

### 57. ROI Index Caching
_Pre-computes HCP MMP1.0 ROI vertex-index cache to enable fast API server lookups without tribev2 import overhead._

- `services\inference\scripts\cache_roi.py`

### 58. Ising Alpha Calibration
_Estimates opinion-dynamics coupling parameter from neural arousal asymmetry via empirical regression._

- `services\inference\scripts\calibrate_alpha.py`

### 59. ROI Vertex Export
_Exports HCP brain region-of-interest vertex indices from fsaverage5 mesh to backend cache and frontend visualization._

- `services\inference\scripts\export_roi_vertices.py`

### 60. Brain Surface Masking
_Generates and geometrically validates medial-wall masks for fsaverage5 brain surfaces from FreeSurfer data._

- `services\inference\scripts\gen_medial_mask.py`

### 61. Brain Surface Upsampling
_Creates lookup maps for expanding low-resolution brain surface data onto high-resolution meshes using nearest-neighbor geometry._

- `services\inference\scripts\gen_upsample_maps.py`

### 62. Model Weight Prewarming
_Script pre-downloads ML model weights (gTTS, WhisperX, LLaMA, Wav2Vec-BERT) to mounted cache before inference serving to eliminate request-time download latency._

- `services\inference\scripts\prewarm.py`

### 63. Inference Deployment Validation
_Smoke test that verifies deployment environment health for TRIBE v2 inference by checking Python/GPU/model dependencies and running a single prediction round-trip._

- `services\inference\scripts\smoke_test.py`

### 64. Inference Test Fixtures
_Pytest configuration providing shared test fixtures for inference tests, including ROI cache mocking to avoid tribev2 dependency._

- `services\inference\tests\conftest.py`

### 65. FastAPI Boot Tests
_Smoke test verifying app startup and health endpoint work with model loading disabled._

- `services\inference\tests\test_app_boot.py`

### 66. Auth Middleware Tests
_Tests for APIKeyMiddleware authenticating requests via API keys in the inference service._

- `services\inference\tests\test_auth.py`

### 67. Blob Storage & Serialization
_Tests in-memory blob storage and numpy array serialization/deserialization for inference services._

- `services\inference\tests\test_blob_store.py`

### 68. Inference Service Tests
_Unit tests for TribeInferenceService covering structural paths; GPU model load/predict tested via deployment smoke test._

- `services\inference\tests\test_inference.py`

### 69. Landau Magnetic Analysis
_Test suite for Landau theory phase-transition calculations—equilibrium magnetization, susceptibility curves, physics math independent of external services._

- `services\inference\tests\test_landau.py`

### 70. NAA Inference Testing
_Unit tests for neural analysis computation using cached ROI data fixtures._

- `services\inference\tests\test_naa.py`

### 71. Inference Pooling Tests
_Unit tests for aggregation functions (mean, peak, trimmed-mean pooling) on prediction tensors in the inference service._

- `services\inference\tests\test_pooling.py`

### 72. Rate Limit Middleware
_Token-bucket rate limiting middleware tests for FastAPI services with configurable refill rates and proxy trust._

- `services\inference\tests\test_rate_limit.py`

### 73. Report Testing
_Offline unit and integration tests for the audit-report API endpoint, context builder, and message rendering pipeline._

- `services\inference\tests\test_report.py`

### 74. ROI Inference Tests
_Tests disk-cache fallback path for ROI service inference, with integration tests for live tribev2 lookup skipped if dependencies unavailable._

- `services\inference\tests\test_roi.py`

### 75. Timeseries Playback Tests
_Tests timeseries endpoint playback by injecting frames directly without model dependency._

- `services\inference\tests\test_timeseries.py`

### 76. Inference Tests
_Test suite package initialization for inference service._

- `services\inference\tests\__init__.py`

### 77. Brain Mesh Export
_Converts fsaverage5 brain surfaces to Three.js-compatible formats (JSON, BIN, GLB) for neuroimaging visualization._

- `services\inference\tribev2\scripts\export_brain_mesh.py`

### 78. TRIBE v2 Demo Utils
_Utilities for TribeModel inference demonstrations and event DataFrame construction._

- `services\inference\tribev2\tribev2\demo_utils.py`

### 79. TRIBE Model Export
_Exposes TribeModel from tribev2 inference service as package entry point._

- `services\inference\tribev2\tribev2\__init__.py`

### 80. TRIBE Experiment Grids
_Grid configurations and defaults for TRIBE v2 neuroscience experiments._

- `services\inference\tribev2\tribev2\grids\__init__.py`
