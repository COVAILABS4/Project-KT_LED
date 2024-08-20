import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Route,
  Routes,
  useNavigate,
} from "react-router-dom";
import Dashboard from "./components/Dashboard.jsx";
import Setup from "./components/Setup.jsx";
import Login from "./components/Login.jsx";
import Import from "./components/Import.jsx";
import "./App.css";
import axios from "axios";

function App() {
  const [data, setData] = useState([]);
  const [login, setLogined] = useState(localStorage.getItem("user"));

  useEffect(() => {
    // Call fetchData every second
    const intervalId = setInterval(fetchData, 3000);

    // Cleanup function to clear the interval when the component unmounts
    return () => clearInterval(intervalId);
  }, []);

  const fetchData = () => {
    const ip = window.location.hostname;
    axios
      .get("http://" + ip + ":5000/data")
      .then((response) => {
        setData(response.data);
      })
      .catch((error) => console.log(error));
  };

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/setup"
          element={
            <Setup fetchData={fetchData} setData={setData} data={data} />
          }
        />
        <Route
          path="/dashboard"
          element={
            <Dashboard fetchData={fetchData} setData={setData} data={data} />
          }
        />
        <Route path="/import" element={<Import fetchData={fetchData} />} />
        <Route
          path="/"
          element={
            login == null ? (
              <Login />
            ) : (
              <Dashboard fetchData={fetchData} setData={setData} data={data} />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
