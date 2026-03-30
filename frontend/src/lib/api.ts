import { useAuthStore } from "./store"

const getApiBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://localhost:8000";
};

const API_BASE_URL = getApiBaseUrl();

interface FetchOptions extends RequestInit {
  data?: any
}

class ApiClient {
  private async request<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const { token } = useAuthStore.getState()
    const url = `${API_BASE_URL}${endpoint}`
    
    const headers = new Headers(options.headers || {})
    if (token) {
      headers.set("Authorization", `Bearer ${token}`)
    }
    
    if (options.data) {
      headers.set("Content-Type", "application/json")
      options.body = JSON.stringify(options.data)
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      if (response.status === 401) {
        useAuthStore.getState().logout()
        window.location.href = "/login"
      }
      
      let errorMessage = `API error: ${response.status}`
      try {
        const errorData = await response.json()
        errorMessage = errorData.message || errorData.detail || errorMessage
      } catch (e: unknown) {
        // Fallback if not JSON
      }
      
      throw new Error(errorMessage)
    }

    return response.json()
  }

  get<T>(endpoint: string, options?: Omit<FetchOptions, "method">) {
    return this.request<T>(endpoint, { ...options, method: "GET" })
  }

  post<T>(endpoint: string, data: any, options?: Omit<FetchOptions, "method" | "data">) {
    return this.request<T>(endpoint, { ...options, method: "POST", data })
  }

  put<T>(endpoint: string, data: any, options?: Omit<FetchOptions, "method" | "data">) {
    return this.request<T>(endpoint, { ...options, method: "PUT", data })
  }

  patch<T>(endpoint: string, data: any, options?: Omit<FetchOptions, "method" | "data">) {
    return this.request<T>(endpoint, { ...options, method: "PATCH", data })
  }

  delete<T>(endpoint: string, options?: Omit<FetchOptions, "method">) {
    return this.request<T>(endpoint, { ...options, method: "DELETE" })
  }
}

const api = new ApiClient()
export default api
