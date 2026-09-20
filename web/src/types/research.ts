export interface ResearchManifest {
  dataset_version: string;
  dataset_name: string;
  protocol_version: string;
  git_commit_sha: string;
  timestamp_utc: string;
  solver_backend: string;
  total_evaluations: number;
  materials: {
    matrix: {
      name: string;
      conductivity_W_mK: number;
      density_kg_m3: number;
      specific_heat_J_kgK: number;
      verification_status: string;
    };
    inclusion: {
      name: string;
      conductivity_W_mK: number;
      density_kg_m3: number;
      specific_heat_J_kgK: number;
      verification_status: string;
    };
  };
  geometries: {
    diameters_mm: number[];
    depths_mm: number[];
    thickness_mm: number;
    plate_dimensions_mm: number[];
    healthy_controls_evaluated: number;
  };
  noise_protocol: {
    levels_snr_db: number[];
    seeds: number[];
    evaluations_per_case: number;
  };
}

export interface MethodSummary {
  method: string;
  total_runs: number;
  detection_rate: number;
  detection_rate_pct: number;
  mean_cnr: number;
  std_cnr: number;
  mean_iou: number;
  std_iou: number;
  mean_dice: number;
  std_dice: number;
  mean_loc_error_detected_mm: number | null;
  std_loc_error_detected_mm: number | null;
  mean_loc_error_all_mm: number | null;
  std_loc_error_all_mm: number | null;
  mean_loc_error_mm: number | null;
  std_loc_error_mm: number | null;
  mean_runtime_ms: number;
  std_runtime_ms: number;
}

export interface DepthSummary {
  method: string;
  depth_mm: number;
  detection_rate: number;
  mean_cnr: number;
  std_cnr?: number;
  mean_iou: number;
  std_iou?: number;
  mean_loc_error_detected_mm: number | null;
  std_loc_error_detected_mm?: number | null;
  mean_loc_error_mm: number | null;
  std_loc_error_mm?: number | null;
}

export interface DiameterSummary {
  method: string;
  diameter_mm: number;
  detection_rate: number;
  mean_cnr: number;
  std_cnr?: number;
  mean_iou: number;
  std_iou?: number;
  mean_loc_error_detected_mm: number | null;
  std_loc_error_detected_mm?: number | null;
  mean_loc_error_mm: number | null;
  std_loc_error_mm?: number | null;
}

export interface NoiseSummary {
  method: string;
  noise_condition: string;
  detection_rate: number;
  mean_cnr: number;
  std_cnr?: number;
  mean_iou: number;
  std_iou?: number;
  mean_loc_error_detected_mm: number | null;
  mean_loc_error_mm: number | null;
}

export interface HealthySummary {
  method: string;
  noise_condition: string;
  total_evaluations: number;
  false_positive_count: number;
  false_positive_rate: number;
  specificity_pct: number;
}

export interface MaxDepthRecord {
  method: string;
  diameter_mm: number;
  noise_condition: string;
  max_detectable_depth_mm: number;
  satisfies_80pct_criterion: boolean;
}

export interface SensitivityRecord {
  variation: string;
  parameter: string;
  percentage_change: number;
  peak_surface_temp_rise_k: number;
  peak_defect_thermal_contrast_k: number;
  pct_cnr: number;
  pct_iou: number;
  pct_loc_error_mm: number | null;
  is_detected: boolean;
}

export interface MetricEvaluation {
  method_name: string;
  iou: number | null;
  dice: number | null;
  precision: number | null;
  recall: number | null;
  localization_error_detected_mm: number | null;
  localization_error_all_mm: number | null;
  localization_error_mm: number | null;
  localization_error_px: number | null;
  cnr: number;
  defect_contrast: number;
  candidate_detected: boolean;
  is_detected: boolean;
  is_false_positive: boolean;
  runtime_seconds?: number;
  runtime_s?: number;
  diameter_error_mm?: number | null;
  area_error_mm2?: number | null;
  true_diameter_mm?: number;
  predicted_diameter_mm?: number | null;
  true_centroid_mm?: number[];
  predicted_centroid_mm?: number[] | null;
}

export interface CaseFrame {
  frame_index: number;
  time_seconds: number;
  image_url: string;
  min_temp_c: number;
  max_temp_c: number;
  mean_temp_c: number;
}

export interface CaseNoiseScenario {
  comparison_image_url: string;
  metrics: MetricEvaluation[];
}

export interface CaseManifest {
  case_tag: string;
  diameter_mm: number;
  depth_mm: number;
  is_healthy: boolean;
  ground_truth: {
    center_x_mm: number;
    center_y_mm: number;
    depth_mm: number;
    diameter_mm: number;
    thickness_mm: number;
    material_name: string;
    area_mm2: number;
    volume_mm3: number;
    has_defect: boolean;
  };
  frames: CaseFrame[];
  noise_scenarios: Record<string, CaseNoiseScenario>;
}

export interface CaseIndexItem {
  case_tag: string;
  diameter_mm: number;
  depth_mm: number;
  is_healthy: boolean;
  preview_url: string;
}