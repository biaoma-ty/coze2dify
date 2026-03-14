import axios from "axios";

const apiBaseUrl = process.env.UMI_APP_API_BASE_URL || "/api/v1";

const client = axios.create({ baseURL: apiBaseUrl });

export default client;
