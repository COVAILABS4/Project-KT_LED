/* eslint-disable react/prop-types */
import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Form,
  Button,
  Card,
  Container,
  Row,
  Col,
  Alert,
} from "react-bootstrap";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./Setup.css";
import "react-tooltip/dist/react-tooltip.css";
import { Tooltip } from "react-tooltip";

import Select from "react-select";

const ip = window.location.hostname;

const colors = [
  { name: "Red", value: "255,0,0" },
  { name: "Green", value: "0,255,0" },
  { name: "Blue", value: "0,0,255" },
  { name: "Yellow", value: "255,255,0" },
  { name: "Cyan", value: "0,255,255" },
  { name: "Magenta", value: "255,0,255" },
  { name: "Orange", value: "255,165,0" },
  { name: "Purple", value: "128,0,128" },
  { name: "Brown", value: "165, 42, 42" },
  { name: "Lime", value: "0,255,123" },
];

const Setup = ({
  fetchData,
  groups,
  racks,
  bins,
  availableDevices,
  availableStaticDevices,
  forSetIP,
  AllStaticDevices,
  slaveDevices,
}) => {
  //For Add Group
  const [newGroupId, setNewGroupId] = useState("");
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    if (!newGroupId) newErrors.newGroupId = "Station Name is required.";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleAddGroup = () => {
    if (!validateForm()) return;

    axios
      .post("http://" + ip + ":5000/new/group", {
        newGroupId: newGroupId,
      })
      .then((response) => {
        notify("Station added successfully!", "success");
        setNewGroupId("");
        setErrors({}); // Clear errors upon successful addition

        // Update local state to show the new group
        // setGroups((prevGroups) => [...prevGroups, { group_id: newGroupId }]);
      })
      .catch((error) => notify("Failed to add Station", "error"));
  };

  const handleDeleteGroup = async (groupId) => {
    try {
      await axios.post("http://" + ip + ":5000/delete/group", { groupId });
      notify("Station deleted successfully!", "success");

      // Remove the deleted group from the local state
      // setGroups((prevGroups) =>
      //   prevGroups.filter((group) => group.group_id !== groupId)
      // );
    } catch (error) {
      notify("Failed to delete group", "error");
    }
  };

  //-------------------------END of GROUP----------------------------------------------//

  const [groupIdForWrack, setGroupIdForWrack] = useState("");
  const [newWrackId, setNewWrackId] = useState("");
  const [kitId, setKitId] = useState(""); // New state for KIT_ID

  const groupOptions = groups.map((group) => ({
    value: group.group_id,
    label: group.group_id,
  }));

  const handleAddWrack = () => {
    if (!groupIdForWrack || !newWrackId || !kitId) {
      notify("Please fill in all fields before adding a rack.", "warning");
      return;
    }

    axios
      .post("http://" + ip + ":5000/new/rack", {
        Groupid: groupIdForWrack,
        newWrackid: newWrackId,
        kitId: `KT-${kitId}`,
      })
      .then((response) => {
        notify("Rack added successfully!", "success");
        setNewWrackId("");
        setKitId("");
        // Optionally refresh or re-fetch racks list after adding a new one
      })
      .catch((error) => {
        console.error("Error adding rack:", error);
        notify("Failed to add rack", "error");
      });
  };

  // Function to delete a rack
  const handleDeleteRack = (rack) => {
    axios
      .post("http://" + ip + ":5000/delete/rack", {
        Groupid: groupIdForWrack,
        rackId: rack.rack_id,
      })
      .then((response) => {
        notify("Rack deleted successfully!", "success");
        // Optionally refresh or re-fetch racks list after deleting one
      })
      .catch((error) => {
        console.error("Error deleting rack:", error);
        notify("Failed to delete rack", "error");
      });
  };

  //-------------------------END  of Add Rack-----------------------------------------//
  const [groupIdForSchedule, setGroupIdForSchedule] = useState("");
  const [wrackIdForSchedule, setWrackIdForSchedule] = useState("");
  const [binIdForSchedule, setBinIdForSchedule] = useState("");
  const [scheduleTime, setScheduleTime] = useState("");
  const [selectedColor, setSelectedColor] = useState("");

  const notify = (message, type) => {
    toast[type](message, {
      position: "top-right",
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      progress: undefined,
    });

    fetchData();
  };

  const handleAddSchedule = () => {
    // Validation before adding a schedule
    if (
      !groupIdForSchedule ||
      !wrackIdForSchedule ||
      !binIdForSchedule ||
      !scheduleTime ||
      !selectedColor
    ) {
      notify("Please fill in all fields!", "warning");
      return;
    }

    function normalizeColor(color) {
      return Math.round((color / 255) * 65);
    }

    const newSchedule = {
      time: scheduleTime,
      enabled: true,
      color: selectedColor.split(",").map(Number),
      colorESP: selectedColor.split(",").map(Number).map(normalizeColor),
    };

    axios
      .post("http://" + ip + ":5000/new/schedule", {
        group_id: groupIdForSchedule,
        wrack_id: wrackIdForSchedule,
        bin_id: wrackIdForSchedule + binIdForSchedule,
        new_schduled: newSchedule,
      })
      .then((response) => {
        notify("Schedule added successfully!", "success");
        // Reset form fields
        // setGroupIdForSchedule("");
        // setWrackIdForSchedule("");
        // setBinIdForSchedule("");
        setScheduleTime("");
        setSelectedColor("");
      })
      .catch((error) => notify("Failed to add schedule", "error"));
  };

  const handleColorSelect = (colorValue) => {
    setSelectedColor(colorValue);
  };

  const handleDeleteSchedule = (
    groupIdForSchedule,
    wrackIdForSchedule,
    binIdForSchedule,
    scheduleIndex
  ) => {
    const requestData = {
      group_id: groupIdForSchedule,
      wrack_id: wrackIdForSchedule,
      bin_id: binIdForSchedule,
      scheduleIndex: scheduleIndex,
    };

    axios
      .post("http://" + ip + ":5000/delete/schedule", requestData)
      .then((response) => {
        notify("Schedule deleted successfully!", "success");
        // Refresh or re-fetch racks here if needed
      })
      .catch((error) => notify("Failed to delete Schedule", "error"));
  };

  const wrackOptions = racks
    .filter((rack) => rack.group_id === groupIdForSchedule)
    .flatMap((rack) =>
      rack.racks.map((wrack) => {
        // const binCount = wrack.bins ? wrack.bins.length : 0; // Safely check for bins and calculate length
        return {
          value: wrack.rack_id,
          label: `${wrack.rack_id} `,
        };
      })
    );

  // console.log(racks);

  const binOptions = ["_01", "_02", "_03", "_04"].map((num) => ({
    value: num,
    label: `${wrackIdForSchedule}${num}`,
  }));

  return (
    <Container className="setup">
      <h1>Setup</h1>
      <ToastContainer />
      <Row>
        <Col md={4}>
          <Card
            className="setup-card"
            style={{
              borderRadius: "10px",
              boxShadow: "0 4px 8px rgba(0, 0, 0, 0.2)",
            }}
          >
            <Card.Body>
              <Card.Title style={{ color: "#007bff", fontWeight: "bold" }}>
                Add Station
              </Card.Title>
              <Form>
                <Form.Group controlId="newGroupId">
                  <Form.Label>New Station Name</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Enter Station Name"
                    value={newGroupId || ""}
                    onChange={(e) => setNewGroupId(e.target.value)}
                    isInvalid={!!errors.newGroupId}
                  />
                  {errors.newGroupId && (
                    <Form.Control.Feedback type="invalid">
                      {errors.newGroupId}
                    </Form.Control.Feedback>
                  )}
                </Form.Group>
                <Button
                  className="w-100 mt-3"
                  variant="primary"
                  onClick={handleAddGroup}
                  disabled={!newGroupId}
                >
                  Add
                </Button>
              </Form>

              {/* Division for Existing Groups */}
              {groups.length !== 0 && (
                <Card.Title className="mt-4">Existing Stations</Card.Title>
              )}
              {groups.length > 0 && (
                <div
                  className="existing-groups mt-3"
                  style={{ maxHeight: "110px", overflowY: "auto" }}
                >
                  {groups.map((group, index) => (
                    <div
                      key={index}
                      className="d-flex justify-content-between align-items-center mb-2"
                    >
                      <p className="mb-0">
                        {index + 1}: {group.group_id}
                      </p>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDeleteGroup(group.group_id)}
                        className="ml-2"
                      >
                        Delete
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        <Col md={4}>
          <Card
            className="setup-card"
            style={{
              borderRadius: "10px",
              boxShadow: "0 4px 8px rgba(0, 0, 0, 0.2)",
            }}
          >
            <Card.Body>
              <Card.Title style={{ color: "#007bff", fontWeight: "bold" }}>
                Add Rack
              </Card.Title>
              <Form>
                {/* Dropdown for selecting Group ID */}
                <Form.Group controlId="groupIdForWrack">
                  <Form.Label>Station Name</Form.Label>
                  <Select
                    options={groupOptions}
                    value={groupOptions.find(
                      (option) => option.value === groupIdForWrack
                    )}
                    onChange={(selectedOption) =>
                      setGroupIdForWrack(
                        selectedOption ? selectedOption.value : ""
                      )
                    }
                    isSearchable={true}
                    isClearable
                    placeholder="Select Station"
                    noOptionsMessage={() => "No Station"}
                    maxMenuHeight={160}
                  />
                </Form.Group>

                {/* Display existing racks for the selected group */}
                {groupIdForWrack && (
                  <div
                    className="existing-racks"
                    style={{
                      marginTop: "20px",
                      maxHeight: "150px",
                      overflowY: "auto",
                      padding: "10px",
                      border: "1px solid #dee2e6",
                      borderRadius: "5px",
                    }}
                  >
                    <h5 style={{ color: "#343a40" }}>
                      {(() => {
                        const filteredRacks = racks.filter(
                          (rack) => rack.group_id === groupIdForWrack
                        );

                        if (
                          filteredRacks.length > 0 &&
                          filteredRacks[0].racks.length > 0
                        ) {
                          return "Existing Racks in " + groupIdForWrack;
                        } else {
                          return "No Racks found";
                        }
                      })()}
                    </h5>

                    {/* Map through the filtered racks and display them */}
                    {racks
                      .filter((rack) => rack.group_id === groupIdForWrack)
                      .map((rackItem, index) => (
                        <div key={index} style={{ marginBottom: "10px" }}>
                          {rackItem.racks.map((rack, rackIndex) => {
                            // console.log(rack);

                            return (
                              <div
                                key={rackIndex}
                                style={{
                                  display: "flex",
                                  justifyContent: "space-between",
                                  alignItems: "center",
                                  padding: "5px",
                                  borderRadius: "5px",
                                  border: "1px solid #007bff",
                                  marginBottom: "5px",
                                }}
                              >
                                <p
                                  style={{
                                    margin: 0,
                                    fontWeight: "bold",
                                    color: "#007bff",
                                  }}
                                >
                                  {rackIndex + 1} : {" " + rack.rack_id} (
                                  {rack.kit_id})
                                </p>
                                <Button
                                  variant="danger"
                                  size="sm"
                                  onClick={() => handleDeleteRack(rack)}
                                  style={{ borderRadius: "5px" }}
                                >
                                  Delete
                                </Button>
                              </div>
                            );
                          })}
                        </div>
                      ))}
                  </div>
                )}

                {/* Input for New Rack ID */}
                <Form.Group
                  controlId="newWrackId"
                  style={{ marginTop: "20px" }}
                >
                  <Form.Label>New Rack ID</Form.Label>
                  <Form.Control
                    type="text"
                    value={newWrackId}
                    onChange={(e) => setNewWrackId(e.target.value)}
                    placeholder="Enter new rack ID"
                  />
                </Form.Group>

                {/* Input for KIT_ID */}
                <Form.Group controlId="kitId" style={{ marginTop: "20px" }}>
                  <Form.Label>KIT NO</Form.Label>
                  <Form.Control
                    type="number"
                    value={kitId}
                    onChange={(e) => setKitId(e.target.value)}
                    placeholder="Enter KIT No"
                  />
                </Form.Group>

                <p>{kitId === "" ? "" : `KIT ID :  KT-${kitId} `}</p>

                {/* Button to Add Rack */}
                <Button
                  variant="primary"
                  onClick={handleAddWrack}
                  style={{
                    marginTop: "20px",
                    width: "100%",
                    borderRadius: "5px",
                  }}
                  disabled={!newWrackId || !kitId}
                >
                  Add Rack
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>

        <Col md={4}>
          <Card
            className="setup-card"
            style={{
              borderRadius: "10px",
              boxShadow: "0 4px 8px rgba(0, 0, 0, 0.2)",
            }}
          >
            <Card.Body>
              <Card.Title style={{ color: "#007bff", fontWeight: "bold" }}>
                Add Schedule
              </Card.Title>
              <Form>
                {/* React-Select for Group ID */}
                <Form.Group controlId="groupIdForSchedule">
                  <Form.Label>Station Name</Form.Label>
                  <Select
                    options={groupOptions}
                    value={
                      groupOptions.find(
                        (option) => option.value === groupIdForSchedule
                      ) || ""
                    }
                    onChange={(selectedOption) =>
                      setGroupIdForSchedule(
                        selectedOption ? selectedOption.value : ""
                      )
                    }
                    placeholder="Select Station"
                    noOptionsMessage={() => "No Stations"}
                  />
                </Form.Group>

                {/* React-Select for Rack ID */}
                <Form.Group controlId="wrackIdForSchedule">
                  <Form.Label>Rack ID</Form.Label>
                  <Select
                    options={wrackOptions}
                    value={
                      wrackOptions.find(
                        (option) => option.value === wrackIdForSchedule
                      ) || ""
                    }
                    onChange={(selectedOption) =>
                      setWrackIdForSchedule(
                        selectedOption ? selectedOption.value : ""
                      )
                    }
                    placeholder="Select Rack"
                    isDisabled={!groupIdForSchedule}
                  />
                </Form.Group>

                {/* React-Select for Bin ID */}
                <Form.Group controlId="binIdForSchedule">
                  <Form.Label>Bin ID</Form.Label>
                  <Select
                    options={binOptions}
                    value={
                      binOptions.find(
                        (option) => option.value === binIdForSchedule
                      ) || ""
                    }
                    onChange={(selectedOption) =>
                      setBinIdForSchedule(
                        selectedOption ? selectedOption.value : ""
                      )
                    }
                    placeholder="Select Bin"
                    isDisabled={!wrackIdForSchedule}
                  />
                </Form.Group>

                {/* Display existing schedules for the selected bin */}
                {binIdForSchedule && (
                  <h5 style={{ color: "#343a40" }}>
                    Existing Schedules for{" "}
                    {wrackIdForSchedule + binIdForSchedule}:
                  </h5>
                )}
                {binIdForSchedule &&
                  bins
                    .filter(
                      (bin) =>
                        bin.group_id === groupIdForSchedule &&
                        bin.rack_id === wrackIdForSchedule
                    )
                    .map((filteredBin, index) => {
                      const schedules = filteredBin["bin" + binIdForSchedule];

                      return (
                        <div
                          key={index}
                          className="existing-schedules"
                          style={{
                            marginTop: "20px",
                            maxHeight: "150px",
                            overflowY: "auto",
                          }}
                        >
                          {schedules && schedules.length > 0 ? (
                            schedules.map((scheduleItem, scheduleIndex) => (
                              <div
                                key={scheduleIndex}
                                style={{
                                  display: "flex",
                                  justifyContent: "space-between",
                                  alignItems: "center",
                                  padding: "10px",
                                  backgroundColor: `rgb(${scheduleItem.color.join(
                                    ","
                                  )})`,
                                  borderRadius: "5px",
                                  marginBottom: "10px",
                                  border: scheduleItem.enabled
                                    ? "2px solid #007bff"
                                    : "1px solid #ccc",
                                }}
                              >
                                <p
                                  style={{
                                    margin: 0,
                                    fontWeight: "bold",
                                    color: `rgb(${scheduleItem.color
                                      .map((color) => 255 - color)
                                      .join(",")})`,
                                  }}
                                >
                                  {scheduleIndex + 1}
                                  {" : "} {scheduleItem.time}{" "}
                                  {scheduleItem.enabled && "(enabled)"}
                                </p>
                                <Button
                                  variant="danger"
                                  size="sm"
                                  onClick={() =>
                                    handleDeleteSchedule(
                                      groupIdForSchedule,
                                      wrackIdForSchedule,
                                      `${wrackIdForSchedule}${binIdForSchedule}`,
                                      scheduleIndex
                                    )
                                  }
                                  style={{ borderRadius: "5px" }}
                                >
                                  Delete
                                </Button>
                              </div>
                            ))
                          ) : (
                            <p>No schedules available for this bin.</p>
                          )}
                        </div>
                      );
                    })}

                {/* Input for Schedule Time */}
                <Form.Group
                  controlId="scheduleTime"
                  style={{ marginTop: "20px" }}
                >
                  <Form.Label>Schedule Time</Form.Label>
                  <Form.Control
                    type="time"
                    value={scheduleTime || ""}
                    onChange={(e) => setScheduleTime(e.target.value)}
                  />
                </Form.Group>

                {/* Color Selector */}
                <Form.Group controlId="color" style={{ marginTop: "10px" }}>
                  <Form.Label>Color</Form.Label>
                  <div className="color-selector">
                    {colors.map((color, index) => (
                      <div
                        data-tooltip-id={`tooltip-${index}`}
                        data-tooltip-content={color.name}
                        data-tooltip-place="top"
                        key={index}
                        className="color-box"
                        style={{
                          backgroundColor: `rgb(${color.value})`,
                          border:
                            selectedColor === color.value
                              ? "2px solid black"
                              : "none",
                        }}
                        onClick={() => handleColorSelect(color.value)}
                      >
                        {/* Tooltip for color */}
                        <Tooltip id={`tooltip-${index}`} />
                      </div>
                    ))}
                  </div>
                </Form.Group>

                {/* Button to Add Schedule */}
                <Button
                  variant="primary"
                  onClick={handleAddSchedule}
                  style={{
                    marginTop: "20px",
                    width: "100%",
                    borderRadius: "5px",
                  }}
                  disabled={
                    !groupIdForSchedule ||
                    !wrackIdForSchedule ||
                    !binIdForSchedule ||
                    !scheduleTime ||
                    !selectedColor
                  }
                >
                  Add Schedule
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Setup;
