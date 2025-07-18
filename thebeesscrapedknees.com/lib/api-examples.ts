import { Json } from "./supabase/db.types";

// Example API usage - This file demonstrates how to use the CRUD APIs
// You can run this in a browser console or Node.js environment

const API_BASE = "/api"; // Adjust if needed

// Helper function for API calls
async function apiCall(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "API call failed");
  }

  return data;
}

// Profile API Examples
export const profileAPI = {
  // Get current user's profile
  async getMyProfile() {
    return apiCall("/profiles");
  },

  // Get specific profile by ID
  async getProfile(id: string) {
    return apiCall(`/profiles?id=${id}`);
  },

  // Create a new profile
  async createProfile(profileData: {
    nickname: string;
    bio?: string;
    avatar_url?: string;
  }) {
    return apiCall("/profiles", {
      method: "POST",
      body: JSON.stringify(profileData),
    });
  },

  // Update profile
  async updateProfile(
    id: string,
    updates: { nickname?: string; bio?: string; avatar_url?: string }
  ) {
    return apiCall("/profiles", {
      method: "PUT",
      body: JSON.stringify({ id, ...updates }),
    });
  },

  // Delete profile
  async deleteProfile(id: string) {
    return apiCall(`/profiles?id=${id}`, { method: "DELETE" });
  },
};

// Pages API Examples
export const pagesAPI = {
  // Get all pages with pagination
  async getPages(limit = 10, offset = 0) {
    return apiCall(`/pages?limit=${limit}&offset=${offset}`);
  },

  // Get specific page
  async getPage(id: string) {
    return apiCall(`/pages?id=${id}`);
  },

  // Create a new page
  async createPage(pageData: { goal: string; url: string }) {
    return apiCall("/pages", {
      method: "POST",
      body: JSON.stringify(pageData),
    });
  },

  // Update page
  async updatePage(id: string, updates: { goal?: string; url?: string }) {
    return apiCall("/pages", {
      method: "PUT",
      body: JSON.stringify({ id, ...updates }),
    });
  },

  // Delete page
  async deletePage(id: string) {
    return apiCall(`/pages?id=${id}`, { method: "DELETE" });
  },
};

// Page ETL API Examples
export const pageEtlAPI = {
  // Get ETL configurations with optional filtering
  async getEtlConfigs(
    options: {
      id?: string;
      page_id?: string;
      limit?: number;
      offset?: number;
    } = {}
  ) {
    const params = new URLSearchParams();
    if (options.id) params.append("id", options.id);
    if (options.page_id) params.append("page_id", options.page_id);
    if (options.limit) params.append("limit", options.limit.toString());
    if (options.offset) params.append("offset", options.offset.toString());

    return apiCall(`/page-etl?${params}`);
  },

  // Create ETL configuration
  async createEtlConfig(data: {
    page_id: string;
    goal: string;
    url: string;
    function_name?: string;
    function_code?: string;
  }) {
    return apiCall("/page-etl", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Update ETL configuration
  async updateEtlConfig(
    id: string,
    updates: {
      goal?: string;
      url?: string;
      function_name?: string;
      function_code?: string;
    }
  ) {
    return apiCall("/page-etl", {
      method: "PUT",
      body: JSON.stringify({ id, ...updates }),
    });
  },

  // Delete ETL configuration
  async deleteEtlConfig(id: string) {
    return apiCall(`/page-etl?id=${id}`, { method: "DELETE" });
  },
};

// ETL Run API Examples
export const etlRunAPI = {
  // Get ETL runs
  async getEtlRuns(
    options: {
      id?: string;
      etl_run_id?: string;
      limit?: number;
      offset?: number;
    } = {}
  ) {
    const params = new URLSearchParams();
    if (options.id) params.append("id", options.id);
    if (options.etl_run_id) params.append("etl_run_id", options.etl_run_id);
    if (options.limit) params.append("limit", options.limit.toString());
    if (options.offset) params.append("offset", options.offset.toString());

    return apiCall(`/etl-run?${params}`);
  },

  // Create ETL run
  async createEtlRun(data: {
    etl_run_id: string;
    input: Json;
    output: Json;
    url: string;
  }) {
    return apiCall("/etl-run", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Update ETL run
  async updateEtlRun(
    id: string,
    updates: {
      input?: Json;
      output?: Json;
      url?: string;
    }
  ) {
    return apiCall("/etl-run", {
      method: "PUT",
      body: JSON.stringify({ id, ...updates }),
    });
  },

  // Delete ETL run
  async deleteEtlRun(id: string) {
    return apiCall(`/etl-run?id=${id}`, { method: "DELETE" });
  },
};

// Example usage workflow
export async function exampleWorkflow() {
  try {
    // 1. Create a profile
    const profile = await profileAPI.createProfile({
      nickname: "testuser",
      bio: "A test user profile",
    });
    console.log("Created profile:", profile);

    // 2. Create a page
    const page = await pagesAPI.createPage({
      goal: "Scrape product data from e-commerce site",
      url: "https://example-shop.com/products",
    });
    console.log("Created page:", page);

    // 3. Create ETL configuration for the page
    const etlConfig = await pageEtlAPI.createEtlConfig({
      page_id: page.data.id,
      goal: "Extract product information including price, title, and description",
      url: page.data.url,
      function_name: "extractProductData",
      function_code: `
        function extractProductData(html) {
          // Extract product data from HTML
          return {
            title: document.querySelector('.product-title').textContent,
            price: document.querySelector('.price').textContent,
            description: document.querySelector('.description').textContent
          };
        }
      `,
    });
    console.log("Created ETL configuration:", etlConfig);

    // 4. Create an ETL run record
    const etlRun = await etlRunAPI.createEtlRun({
      etl_run_id: etlConfig.data.id,
      input: { url: page.data.url, timestamp: new Date().toISOString() },
      output: {
        title: "Sample Product",
        price: "$29.99",
        description: "A great product with amazing features",
        extracted_at: new Date().toISOString(),
      },
      url: page.data.url,
    });
    console.log("Created ETL run:", etlRun);

    // 5. Get all pages with pagination
    const allPages = await pagesAPI.getPages(10, 0);
    console.log("All pages:", allPages);

    return {
      profile: profile.data,
      page: page.data,
      etlConfig: etlConfig.data,
      etlRun: etlRun.data,
    };
  } catch (error) {
    console.error("Workflow error:", error);
    throw error;
  }
}

// Export for use in other files
const apiHelpers = {
  profileAPI,
  pagesAPI,
  pageEtlAPI,
  etlRunAPI,
  exampleWorkflow,
};

export default apiHelpers;
