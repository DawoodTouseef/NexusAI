
import {
    GoogleGenerativeAI,
    HarmCategory,
    HarmBlockThreshold,
} from "@google/generative-ai";
import axios from "axios";
import axiosInstance from "../utils/axios"

const url="http://127.0.0.1:5000"
const MODEL_NAME = "gemini-1.0-pro";
const API_KEY = "AIzaSyAGdEZLRMpGx1VLy-iK4kKDUApSa5z_YZQ";

export async function runChat(prompt) {
    const genAI = new GoogleGenerativeAI(API_KEY);
    const model = genAI.getGenerativeModel({ model: MODEL_NAME });

    const generationConfig = {
        temperature: 0.9,
        topK: 1,
        topP: 1,
        maxOutputTokens: 2048,
    };

    const safetySettings = [
        {
            category: HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        },
        {
            category: HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        },
        {
            category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        },
        {
            category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        },
    ];

    const chat = model.startChat({
        generationConfig,
        safetySettings,
        history: [
        ],
    });

    const result = await chat.sendMessage(prompt);
    const response = result.response;
    console.log(response.text());
    return response.text();
}
export async function runlocal(prompt,file=null){
    const messages={
        "messages":[{
            "role":"user",
            "content":prompt
        }],
    }
    if(file){
        messages.files=file;
    }
    const response  = await axiosInstance.post('chat/', messages);
    
    const data =await response.data;
    return data.message;
    
}

