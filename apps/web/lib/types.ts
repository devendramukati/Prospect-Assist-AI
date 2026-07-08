export type Tier = "Serious" | "Quality" | "Interested" | "Not Qualified";

export interface LeadSummary {
  external_ref: string;
  employment_type: string;
  tier: Tier;
  composite_score: number;
  capped_by: "intent_gate" | "discipline_gate" | null;
  max_stage: string | null;
  reached_disbursed: boolean;
  discipline_flagged: boolean;
}

export interface LeadsResponse {
  count: number;
  leads: LeadSummary[];
}

export interface KYCProfile {
  full_name: string;
  pan_masked: string;
  phone_masked: string;
  date_of_birth: string;
}

export interface Customer {
  id: string;
  external_ref: string;
  employment_type: string;
  created_at: string;
  kyc?: KYCProfile;
  account_count?: number;
}

export type ConsentStatus = "pending" | "approved" | "denied" | "expired" | "revoked";

export interface FIPInfo {
  fip_id: string;
  name: string;
}

export interface ConsentRequest {
  id: string;
  customer_id: string;
  external_ref: string;
  aa_handle: string;
  fip_id: string;
  fip_name: string;
  purpose: string;
  status: ConsentStatus;
  data_range_from: string;
  data_range_to: string;
  requested_at: string;
  approved_at: string | null;
  expires_at: string;
  data_fetched: boolean;
}

export interface IncomeEstimate {
  method: "fixed_salary" | "rolling_avg" | "turnover_margin";
  monthly_income_estimate: number;
  income_stability_score: number;
  sample_size: number;
  confidence_low: number | null;
  confidence_high: number | null;
  supporting_evidence: Record<string, number>;
}

export interface ExpenseSummary {
  essential_needs: number;
  compulsory_obligations: number;
  discretionary_wants: number;
  savings_investment: number;
  months_observed: number;
}

export interface DisposableIncome {
  disposable_income: number;
  foir_pct: number;
}

export interface AffordabilityProduct {
  max_affordable_emi: number;
  max_affordable_principal: number;
  requires_collateral_input: boolean;
}

export interface DisciplineSignals {
  day1_spend_velocity: { day1_spend_velocity_pct: number; months_observed: number };
  bounce: { bounce_count: number; bounce_flag: boolean };
  balance: { minimum_running_balance: number; low_balance_event_count: number; went_negative: boolean };
}

export interface CapacityAssessment {
  income: IncomeEstimate;
  expense_summary: ExpenseSummary;
  capacity_basis: "net_income" | "turnover";
  capacity_base_income: number;
  disposable_income: DisposableIncome;
  affordability_by_product: Record<string, AffordabilityProduct>;
  discipline: DisciplineSignals;
}

export interface ScoreFactor {
  factor: "intent" | "capacity" | "discipline";
  score: number;
  weight: number;
  contribution: number;
  detail?: string;
}

export interface ScoreExplanation {
  composite_score: number;
  tier: Tier;
  capped_by: "intent_gate" | "discipline_gate" | null;
  gate_reasons: string[];
  factors: ScoreFactor[];
}

export interface CompositeScore {
  scoring_version: string;
  intent_score: number;
  capacity_score: number;
  discipline_score: number;
  composite_score: number;
  tier: Tier;
  capped_by: "intent_gate" | "discipline_gate" | null;
  explanation: ScoreExplanation;
}

export interface LeadExplainResponse {
  customer: Customer;
  assessment: CapacityAssessment;
  score: CompositeScore;
}
