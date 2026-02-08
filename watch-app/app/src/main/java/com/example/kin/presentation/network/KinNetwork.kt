package com.example.kin.presentation.network

import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import com.google.gson.annotations.SerializedName

// 1. Data Models

data class WatchConfig(
    val status: String,
    val animation_url: String,
    val primary_color: String
)

data class ChatRequest(
    // The backend expects "message", so we map your variable to that JSON key
    @SerializedName("message") val message: String
)

data class ChatResponse(
    val reply_text: String,
    val action: String?
)

// 2. API Definition

interface LovableApi {
    @GET("functions/v1/watch-config")
    suspend fun getConfig(): WatchConfig

    @POST("functions/v1/chat")
    suspend fun sendChat(@Body request: ChatRequest): ChatResponse
}

// 3. Singleton Client

object KinClient {
    // ⚠️ IMPORTANT: Update this to your deployed FastAPI backend URL
    // For local testing: "http://10.0.2.2:8000/" (Android emulator)
    // For deployed: "https://your-app.railway.app/" or "https://your-app.onrender.com/"
    private const val BASE_URL = "http://10.0.2.2:8000/"  // TODO: Replace with your deployed URL

    // Device Token for authentication (keep this for security)
    private const val DEVICE_TOKEN = "uPzTmdc37OJLre1H3pXJvkDNesVmLcuk"

    private val client = OkHttpClient.Builder()
        .addInterceptor { chain ->
            val request = chain.request().newBuilder()
                // Custom device authentication
                .addHeader("x-device-token", DEVICE_TOKEN)

                // Content Type
                .addHeader("Content-Type", "application/json")
                .build()
            chain.proceed(request)
        }
        .build()

    val api: LovableApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(LovableApi::class.java)
    }
}