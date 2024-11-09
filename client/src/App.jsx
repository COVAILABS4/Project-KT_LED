import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Dashboard from "./components/Dashboard.jsx";
import Setup from "./components/Setup.jsx";
import Login from "./components/Login.jsx";
import Import from "./components/Import.jsx";
import "./App.css";
import axios from "axios";

function App() {
  const ip = window.location.hostname;
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

  const [length, setLength] = useState(0);

  // Function to fetch the current length from the API
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const fetchLength = async () => {
    try {
      const response = await axios.get("http://" + ip + ":5000/get-length/sta");
      setLength(response.data.length); // Update the state with the fetched length
    } catch (error) {
      console.error("Error fetching length:", error);
    }
  };

  // Function to set a new length via the API
  const setLengthToAPI = async (newLength) => {
    try {
      const response = await axios.post(
        "http://" + ip + ":5000/set-length/sta",
        {
          newLength,
        }
      );
      setLength(response.data.length); // Update the state with the new length
    } catch (error) {
      console.error("Error setting length:", error);
    }
  };

  // Fetch length when the component mounts
  useEffect(() => {
    fetchLength();
  }, [fetchLength]);

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
              setLengthToAPI={setLengthToAPI}
              fetchLength={fetchLength}
              length={length}
              // data={data}
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
