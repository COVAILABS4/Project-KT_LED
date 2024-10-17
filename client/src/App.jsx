import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Dashboard from "./components/Dashboard.jsx";
import Setup from "./components/Setup.jsx";
import Login from "./components/Login.jsx";
import Import from "./components/Import.jsx";
import "./App.css";
import axios from "axios";

function App() {
  const [data, setData] = useState([]);
  const [login, setLogined] = useState(localStorage.getItem("user"));

  const [devices, setDevices] = useState([]);
  const [groups, setGroups] = useState([]);
  const [racks, setRacks] = useState([]);
  const [bins, setBins] = useState([]);

  const [availableDevices, setAvailableDevices] = useState([]);

  const [availableStaticDevices, setAvailableStaticDevices] = useState([]);
  const [AllStaticDevices, setAllStaticDevices] = useState([]);

  const [masterDevices, setMasterDevices] = useState([]);
  const [slaveDevices, setSlaveDevices] = useState([]);

  const [forSetIP, setForSetIP] = useState([]);

  // setInterval(() => {
  //   fetchData();
  // }, 3000);

  useEffect(() => {
    // Call fetchData every second
    const intervalId = setInterval(fetchData, 1000);

    // fetchData();
    // Cleanup function to clear the interval when the component unmounts
    return () => clearInterval(intervalId);
  }, []);

  const processResponseData = (data) => {
    let groupArray = [];
    let racksArray = [];
    let binsArray = [];

    data.forEach((group) => {
      // Populate groups array
      groupArray.push({
        group_id: group.Group_id,
        device_id: group.master_device_id,
      });

      // console.log(groupArray);

      // Populate racks array
      let rackObj = { group_id: group.Group_id, racks: [] };
      group.racks.forEach((rack) => {
        rackObj.racks.push({
          rack_id: rack.rack_id,
          kit_id: rack.KIT_ID,
        });
      });
      racksArray.push(rackObj);

      // Populate bins array
      group.racks.forEach((rack) => {
        let binObj = {
          group_id: group.Group_id,
          rack_id: rack.rack_id,
          bin_01: [],
          bin_02: [],
          bin_03: [],
          bin_04: [],
        };

        rack.bins.forEach((bin, index) => {
          if (index < 4) {
            // assuming only 4 bins per rack
            binObj[`bin_0${index + 1}`] = bin.schedules;
          }
        });

        binsArray.push(binObj);
      });
    });

    // console.log(groupArray, racksArray, binsArray);

    setGroups(groupArray);
    setRacks(racksArray);
    setBins(binsArray);
  };

  const fetchData = () => {
    const ip = window.location.hostname;
    axios
      .get(`http://${ip}:5000/data`)
      .then((response) => {
        const data = response.data;
        setData(data);
        processResponseData(data);
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
            <Setup
              fetchData={fetchData}
              setData={setData}
              data={data}
              groups={groups}
              racks={racks}
              bins={bins}
              availableDevices={availableDevices}
              availableStaticDevices={availableStaticDevices}
              forSetIP={forSetIP}
              AllStaticDevices={AllStaticDevices}
              slaveDevices={slaveDevices}
            />
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
