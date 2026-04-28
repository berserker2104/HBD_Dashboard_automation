import axios from "axios";

const api = axios.create({
  // Direct connection to Flask backend on port 8001
  baseURL: "http://localhost:8001/api", 
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;