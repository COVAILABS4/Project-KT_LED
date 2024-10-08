import React, { useState } from "react";
import { Table, Button } from "react-bootstrap";
import ColorPickerModal from "./ColorPickerModal.jsx";
import "./Dashboard.css";
import axios from "axios";

const BinDetails = ({
  selectedBin,
  setShowBinDetails,
  updateColor,
  toggleSchedule,
  fetchData,
  setSelectedBin,
  handleBinClick,
}) => {
  const ip = window.location.hostname;

  const toggleEnabled = async (group_id, rack_id, bin_id) => {
    try {
      const response = await axios.post(
        "http://" + ip + ":5000/bin/update/enabled",
        {
          group_id,
          rack_id,
          bin_id,
        }
      );
      setSelectedBin(response.data);
      handleBinClick(group_id, rack_id, bin_id);
      fetchData();
    } catch (error) {
      console.error("Error toggling enabled:", error);
    }
  };

  const toggleClicked = async (group_id, rack_id, bin_id) => {
    try {
      const response = await axios.post(
        "http://" + ip + ":5000/bin/update/clicked",
        {
          group_id,
          rack_id,
          bin_id,
        }
      );

      alert("LED TURN OFF Successfully!!!!!!!");

      setShowBinDetails(false);
      setSelectedBin(response.data);
      // setShowBinDetails(true);

      // handleBinClick(group_id, rack_id, bin_id);

      fetchData();
    } catch (error) {
      console.error("Error toggling clicked:", error);
    }
  };

  const [showColorPicker, setShowColorPicker] = useState(false);
  const [newColor, setNewColor] = useState(selectedBin.color);

  const handleColorUpdate = () => {
    updateColor(
      selectedBin.group_id,
      selectedBin.rack_id,
      selectedBin.bin_id,
      newColor
    );
    handleBinClick(
      selectedBin.group_id,
      selectedBin.rack_id,
      selectedBin.bin_id
    );

    setShowColorPicker(false);
  };

  return (
    <div className="bin-details">
      <Button onClick={() => setShowBinDetails(false)} variant="danger">
        Close
      </Button>
      <h3>Bin Details</h3>
      <p>Station Name: {selectedBin.group_id}</p>
      <p>Rack ID: {selectedBin.rack_id}</p>
      <p>Bin ID: {selectedBin.bin_id}</p>
      {/* <div style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
        Color:
        <span>
          <div
            style={{
              width: "25px",
              height: "25px",
              backgroundColor: `rgb(${selectedBin.color.toString()})`,
            }}
          ></div>
        </span>
      </div> */}
      {/* <Button onClick={() => setShowColorPicker(true)}>Update Color</Button> */}
      <div>
        <p>Enabled Status : {selectedBin.enabled.toString()}</p>
        <Button
          onClick={() =>
            toggleEnabled(
              selectedBin.group_id,
              selectedBin.rack_id,
              selectedBin.bin_id
            )
          }
        >
          {selectedBin.enabled ? "Disable" : "Enable"}
        </Button>
      </div>
      <div>
        <p>Current State : {selectedBin.clicked.toString()}</p>
        <Button
          onClick={() =>
            toggleClicked(
              selectedBin.group_id,
              selectedBin.rack_id,
              selectedBin.bin_id
            )
          }
          disabled={selectedBin.clicked} // Disable button when clicked is false
        >
          Turn Off
        </Button>
      </div>
      <h4>Schedules</h4>
      <Table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Color</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {selectedBin.schedules.map((schedule, index) => (
            <tr key={index}>
              <td>{schedule.time}</td>
              <td
                style={{ backgroundColor: `rgb(${schedule.color.join(",")})` }}
              ></td>
              <td>
                <Button
                  onClick={() =>
                    toggleSchedule(
                      selectedBin.group_id,
                      selectedBin.rack_id,
                      selectedBin.bin_id,
                      index,
                      schedule.enabled
                    )
                  }
                >
                  {schedule.enabled ? "Disable" : "Enable"}
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      <ColorPickerModal
        show={showColorPicker}
        handleClose={() => setShowColorPicker(false)}
        handleColorUpdate={handleColorUpdate}
        setNewColor={setNewColor}
      />
    </div>
  );
};

export default BinDetails;
