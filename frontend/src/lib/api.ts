import { useAuthStore } from "./store"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8050"

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
      throw new Error(`API error: ${response.status}`)
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

  delete<T>(endpoint: string, options?: Omit<FetchOptions, "method">) {
    return this.request<T>(endpoint, { ...options, method: "DELETE" })
  }
}

const api = new ApiClient()
export default api
