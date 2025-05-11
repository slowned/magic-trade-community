import axios from "axios";
// import store from "@/store";

const API_URL = "http://127.0.0.1:8008/"
const apiClient = axios.create({
  // ez json mock
  // baseURL: "http://my-json-server.typicode.com/slowned/inmobiliaria/",
  baseURL: API_URL,
  withCredentials: false,
  headers: {
    Accept: "application/json",
  },
});


// // Interceptor para adjuntar el token JWT en cada solicitud si existe en el store
// apiClient.interceptors.request.use(
//   (config) => {
//     const token = store.state.token; // Accede al token desde el store

//     if (token) {
//       config.headers.Authorization = `Bearer ${token}`;
//     }

//     return config;
//   },
//   (error) => {
//     return Promise.reject(error);
//   }
// );

// // Interceptor de respuesta para manejar errores de autenticación
// apiClient.interceptors.response.use(
//   (response) => response,
//   async (error) => {
//     if (error.response && error.response.status === 401) {
//       try {
//         // Intentar refrescar el token si obtenemos un error 401
//         const refreshResponse = await axios.post(`${API_URL}api/token/refresh/`, {
//           refresh: store.state.refreshToken,
//         });
        
//         const newToken = refreshResponse.data.access;

//         // Guardar el nuevo token en el store y actualizar localStorage
//         store.commit("SET_TOKEN", newToken);
//         localStorage.setItem("token", newToken);

//         // Reintentar la solicitud original con el nuevo token
//         error.config.headers.Authorization = `Bearer ${newToken}`;
//         return apiClient.request(error.config);
//       } catch (refreshError) {
//         // Si el refresco falla, forzar logout
//         store.dispatch("logout");
//       }
//     }
//     return Promise.reject(error);
//   }
// );

export default {
  getBinders() {
    return apiClient.get("binders/binders/")
  },
  getBinder(id) {
    return apiClient.get(`binders/binders/${id}`)
  },
  filterBinder(queryParams) {
    return apiClient.get("binders/", { params: queryParams })
  },
  deleteBinder(id) {
    return apiClient.delete(`binders/${id}`)
  },
  createBinder(params) {
    return apiClient.post("binders/binders/", params)
  },
  addCardsToBinder(binderId, cardNames) {
    return apiClient.post(`binders/${binderId}/add-cards/`, { card_names: cardNames });
  },
  cardExists(names) {
    return apiClient.post("cards/check-cards/", names)
  },
  generateToken(credentials) {
    return apiClient.post('api/token/', credentials)
  }
};
