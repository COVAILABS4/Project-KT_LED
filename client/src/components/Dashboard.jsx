import React, { useState, useEffect } from "react";
import axios from "axios";
import { Container } from "react-bootstrap";
import { ToastContainer, toast } from "react-toastify";
import Header from "./Header";
import Groups from "./Groups";
import BinDetails from "./BinDetails";
import "react-toastify/dist/ReactToastify.css";
import "./Dashboard.css";

const Dashboard = ({ data, fetchData }) => {
  const [selectedBin, setSelectedBin] = useState(null);
  const [showBinDetails, setShowBinDetails] = useState(false);

  const ip = window.location.hostname;

  // useEffect(() => {
  //   fetchData();
  // }, [data]);

  const handleBinClick = (group_id, rack_id, bin_id) => {
    console.log(group_id, rack_id, bin_id);
    axios
      .get("http://" + ip + ":5000/bin", {
        params: { group_id, rack_id, bin_id },
      })
      .then((response) => {
        setSelectedBin(response.data);
        setShowBinDetails(true);
      })
      .catch((error) => console.log(error));
  };

  const toggleSchedule = (group_id, rack_id, bin_id, index, current_status) => {
    axios
      .put("http://" + ip + ":5000/bin/update/schedule", {
        group_id,
        rack_id,
        bin_id,
        scheduled_index: index,
        current_enabled_status: current_status,
      })
      .then((response) => {
        setSelectedBin(response.data);
        fetchData();
        toast.success("Schedule updated successfully");
      })
      .catch((error) => console.log(error));
  };

  const updateColor = (group_id, rack_id, bin_id, new_color) => {
    axios
      .put("http://" + ip + ":5000/bin/update/color", {
        group_id,
        rack_id,
        bin_id,
        new_color,
      })
      .then((response) => {
        setSelectedBin(response.data);
        fetchData();
        toast.success("Color updated successfully");
      })
      .catch((error) => console.log(error));
  };

  return (
    <Container fluid className="dashboard">
      <Header fetchData={fetchData} data={data} />
      <Groups data={data} handleBinClick={handleBinClick} />
      {showBinDetails && selectedBin && (
        <BinDetails
          selectedBin={selectedBin}
          setShowBinDetails={setShowBinDetails}
          updateColor={updateColor}
          toggleSchedule={toggleSchedule}
          fetchData={fetchData}
          setSelectedBin={setSelectedBin}
        />
      )}
      <ToastContainer className="toast-container" />
    </Container>
  );
};

export default Dashboard;
