// ---------------------------------------------------------------------------
// Response / shape types
// ---------------------------------------------------------------------------

export interface RecordUsageOptions {
  department?: string;
  jobtitle?: string;
}

export interface RecordUsageResponse {
  status: string;
  monthly_total: number;
  usage_limit: number | null;
  limit_exceeded: boolean | null;
}

export interface RecordUsageBatchResponse {
  status: string;
  monthly_total: number;
  usage_limit: number | null;
  limit_exceeded: boolean | null;
  records_processed: number | null;
}

export interface AppUsage {
  app_name: string;
  total_cost: number;
}

export interface ProfileUsage {
  profile_name: string;
  total_cost: number;
}

export interface DepartmentUsage {
  department: string;
  total_cost: number;
}

export interface CompanyMonthlyUsageResponse {
  company: string;
  year: number;
  month: number;
  total_cost: number;
  per_app: AppUsage[];
  per_profile: ProfileUsage[];
}

export interface UserMonthlyUsageResponse {
  company: string;
  user_email: string;
  year: number;
  month: number;
  total_cost: number;
  per_app: AppUsage[];
  per_profile: ProfileUsage[];
}

export interface UserDetail {
  user_email: string;
  department: string | null;
  jobtitle: string | null;
  total_cost: number;
  per_app: AppUsage[];
  per_profile: ProfileUsage[];
}

export interface CompanyDetail {
  company: string;
  total_cost: number;
  per_app: AppUsage[];
  per_department: DepartmentUsage[];
  per_profile: ProfileUsage[];
  users: UserDetail[];
}

export interface DetailedMonthlyUsageResponse {
  year: number;
  month: number;
  total_cost: number;
  companies: CompanyDetail[];
}

export interface LimitStatusResponse {
  company: string;
  current_usage: number;
  usage_limit: number | null;
  percentage: number | null;
  exceeded: boolean;
}

// ---------------------------------------------------------------------------
// Client options
// ---------------------------------------------------------------------------

export interface UsageManagerClientOptions {
  /** Base URL of the Usage Manager service, e.g. "https://api.example.com" */
  baseUrl: string;
  /** Bearer API key */
  apiKey: string;
  /** Name of the calling application */
  appName: string;
  /** Request timeout in milliseconds (default: 10 000) */
  timeout?: number;
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export class UsageManagerClient {
  private readonly baseUrl: string;
  private readonly appName: string;
  private readonly timeout: number;
  private readonly headers: Record<string, string>;

  constructor(options: UsageManagerClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.appName = options.appName;
    this.timeout = options.timeout ?? 10_000;
    this.headers = {
      Authorization: `Bearer ${options.apiKey}`,
      "Content-Type": "application/json",
    };
  }

  // -------------------------------------------------------------------------
  // Internal fetch helper
  // -------------------------------------------------------------------------

  private async request<T>(
    method: string,
    path: string,
    opts?: {
      body?: unknown;
      params?: Record<string, string | number | undefined>;
    }
  ): Promise<T> {
    let url = `${this.baseUrl}${path}`;

    if (opts?.params) {
      const qs = new URLSearchParams(
        Object.entries(opts.params)
          .filter((entry): entry is [string, string | number] => entry[1] !== undefined)
          .map(([k, v]) => [k, String(v)])
      ).toString();
      if (qs) url += `?${qs}`;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    let response: Response;
    try {
      response = await fetch(url, {
        method,
        headers: this.headers,
        body: opts?.body !== undefined ? JSON.stringify(opts.body) : undefined,
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timer);
    }

    if (!response.ok) {
      const text = await response.text().catch(() => "");
      throw new Error(`HTTP ${response.status} ${response.statusText}: ${text}`);
    }

    return response.json() as Promise<T>;
  }

  // -------------------------------------------------------------------------
  // Public API — mirrors UsageManagerClient (Python)
  // -------------------------------------------------------------------------

  /** Record a single usage entry. */
  async recordUsage(
    company: string,
    userEmail: string,
    profileName: string,
    cost: number,
    options?: RecordUsageOptions
  ): Promise<RecordUsageResponse> {
    return this.request<RecordUsageResponse>("POST", "/usage/record", {
      body: {
        app_name: this.appName,
        company,
        user_email: userEmail,
        profile_name: profileName,
        cost,
        department: options?.department ?? null,
        jobtitle: options?.jobtitle ?? null,
      },
    });
  }

  /** Record a batch of usage entries using the legacy nested users_data shape. */
  async recordUsageBatch(
    company: string,
    usersData: Record<string, unknown>
  ): Promise<RecordUsageBatchResponse> {
    return this.request<RecordUsageBatchResponse>("POST", "/usage/record/batch", {
      body: {
        app_name: this.appName,
        company,
        users_data: usersData,
      },
    });
  }

  /** Get company monthly usage with per-app and per-profile breakdowns. */
  async getCompanyMonthlyUsage(
    company: string,
    year?: number,
    month?: number
  ): Promise<CompanyMonthlyUsageResponse> {
    return this.request<CompanyMonthlyUsageResponse>(
      "GET",
      `/usage/company/${encodeURIComponent(company)}/monthly`,
      { params: { year, month } }
    );
  }

  /** Get user monthly usage with per-app and per-profile breakdowns. */
  async getUserMonthlyUsage(
    company: string,
    userEmail: string,
    year?: number,
    month?: number
  ): Promise<UserMonthlyUsageResponse> {
    return this.request<UserMonthlyUsageResponse>(
      "GET",
      `/usage/company/${encodeURIComponent(company)}/user/${encodeURIComponent(userEmail)}/monthly`,
      { params: { year, month } }
    );
  }

  /** Get a detailed monthly usage report across all companies, or filtered to one company. */
  async getDetailedMonthlyUsage(
    year?: number,
    month?: number,
    company?: string
  ): Promise<DetailedMonthlyUsageResponse> {
    return this.request<DetailedMonthlyUsageResponse>(
      "GET",
      "/usage/monthly/detailed",
      { params: { year, month, company } }
    );
  }

  /** Returns true if the company has exceeded its monthly limit. */
  async checkLimitExceeded(company: string): Promise<boolean> {
    const data = await this.request<{ exceeded: boolean }>(
      "GET",
      `/usage/company/${encodeURIComponent(company)}/limit`
    );
    return data.exceeded;
  }

  /** Get detailed limit status for a company. */
  async getLimitStatus(company: string): Promise<LimitStatusResponse> {
    return this.request<LimitStatusResponse>(
      "GET",
      `/usage/company/${encodeURIComponent(company)}/limit/status`
    );
  }
}
