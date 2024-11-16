/* eslint-disable react/prop-types */
import React, { useState, useEffect, useRef, useMemo } from "react";
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
  length,
  setLengthToAPI,
  data,
  // fetchLength,
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

        setHighlightedGroupIndex(null);
        setFocusState(null);

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

  const AnimatedGroup = ({ groups, newGroupId, highlightedIndex }) => {
    // Handler to add a new station
    const handleAddStation = () => {
      const newLength = length + 1;
      setLengthToAPI(newLength); // Make the API call to update the length
    };

    // Handler to remove a station
    const handleRemoveStation = () => {
      const newLength = length - 1;
      if (newLength >= 0) {
        setLengthToAPI(newLength); // Make the API call to update the length
      }
    };

    return (
      <div
        style={{
          padding: "20px",
          boxShadow: "2px",
          // width: "20px",
          // border: "1px solid black",
          backgroundColor: "white", // Black background
          border: "2px solid grey", // Beautiful #D border
          borderRadius: "10px", // Optional: adds rounded corners to the border
          textAlign: "center", // Aligns the content to the center
          // color: "#000", // White text color for contrast
          width: "500px", // Ensures the div adjusts to its content width
          maxWidth: "80%", // Optional: limits the width for a cleaner look
        }}
      >
        {/* Header Section */}
        <header style={{ textAlign: "center", marginBottom: "20px" }}>
          <h2 style={{ color: "#007bff", fontWeight: "bold" }}>
            Stations Overview
          </h2>
          {/* <p style={{ color: "#555" }}>Manage your stations effectively</p> */}

          {/* Buttons for adding and removing stations */}
          <div style={{ marginBottom: "20px" }}>
            <Button
              variant="primary"
              size="sm" // Smaller size
              onClick={handleAddStation}
              style={{
                marginRight: "10px",
                padding: "5px 12px", // Reduced padding for compact look
                borderRadius: "5px", // Rounded corners
                fontWeight: "500", // Slightly bolder text
              }}
            >
              Add Empty Station
            </Button>
            <Button
              variant="danger"
              size="sm" // Smaller size
              onClick={handleRemoveStation}
              style={{
                padding: "5px 12px", // Reduced padding
                borderRadius: "5px", // Rounded corners
                fontWeight: "500", // Slightly bolder text
              }}
            >
              Remove Empty Station
            </Button>
          </div>
        </header>

        {/* Group Boxes */}
        <Col
          style={{ alignItems: "center" }}
          className="justify-content-center"
        >
          {Array.from({ length }).map((_, index) => (
            <Col key={index} md={5} lg={12} className="mb-3">
              <div
                className={`group-box ${
                  highlightedIndex === index ? "highlighted" : ""
                }`}
                style={{
                  border: "2px solid #007bff",
                  borderRadius: "10px",
                  padding: "8px",
                  textAlign: "center",
                  backgroundColor:
                    highlightedIndex === index
                      ? "#e0f7fa"
                      : !groups[index]
                      ? "#FF7F7F"
                      : "#f9f9f9",
                  cursor: "pointer",
                  transition: "background-color 0.3s ease, transform 0.2s ease",
                  boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
                  transform:
                    highlightedIndex === index ? "scale(1.05)" : "scale(1)",
                }}
              >
                {/* Serial Number */}
                <h5 style={{ color: "#007bff", marginBottom: "10px" }}>
                  Station {index + 1}
                </h5>

                {/* Content */}
                <p
                  style={{
                    fontSize: "16px",
                    fontWeight: "bold",
                    color: "#333",
                  }}
                >
                  {groups[index]
                    ? groups[index].group_id
                    : highlightedIndex === index
                    ? newGroupId === ""
                      ? "..."
                      : newGroupId
                    : "Empty STATION"}
                </p>
              </div>
            </Col>
          ))}
        </Col>
      </div>
    );
  };

  const [highlightedGroupIndex, setHighlightedGroupIndex] = useState(null);

  const [focusState, setFocusState] = useState(null);

  const handleInputFocus = () => {
    setHighlightedGroupIndex(groups.length);
    setFocusState(groups.length);
  };

  const handleMouseEnter = (index) => {
    setHighlightedGroupIndex(index);
  };

  const handleMouseLeave = () => {
    setHighlightedGroupIndex(focusState);
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
        setHighlightedRackIndex(null);

        setFocusRackState(null);
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

  const [highlightedRackIndex, setHighlightedRackIndex] = useState(null);

  const handleMouseEnterRack = (index) => {
    console.log(index + "Enter");
    setHighlightedRackIndex(index);
  };
  const handleMouseLeaveRack = () => {
    console.log(highlightedRackIndex + "OUT");

    setHighlightedRackIndex(focusRackState);

    setFocusRackState(null);
  };

  const [focusRackState, setFocusRackState] = useState(null);

  const handleRackInputFocus = () => {
    let group = data
      ? data.find((group) => group.Group_id === groupIdForWrack)
      : [];
    let length = group.racks ? group.racks.length : null;

    console.log(length);

    setHighlightedRackIndex(length);
    setFocusRackState(length);
  };

  const AnimatedRacks = ({
    highlightedRackIndex,
    group,
    totalRacks = 12,
    newWrackId,
  }) => {
    const racks = [...group.racks];

    let last = racks.length;

    // Fill in missing racks with empty placeholders
    while (racks.length < totalRacks) {
      racks.push({ rack_id: "Empty Rack" });
    }

    return (
      <div
        style={{
          maxWidth: "100%",
          padding: "10px",
          border: "1px solid #ddd",
          borderRadius: "8px",
          backgroundColor: "white",
          boxShadow: "0 4px 10px rgba(0, 0, 0, 0.1)",
          overflow: "auto",
        }}
      >
        <h3
          style={{
            textAlign: "center",
            marginBottom: "15px",
            color: "#007bff",
            fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
            fontWeight: "600",
            textShadow: "1px 1px 1px rgba(0, 0, 0, 0.05)",
          }}
        >
          Rack Overview
        </h3>
        <h4
          style={{
            textAlign: "center",
            marginBottom: "15px",
            color: "#333",
            fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
            fontWeight: "600",
            textShadow: "1px 1px 1px rgba(0, 0, 0, 0.05)",
          }}
        >
          {group.Group_id}
        </h4>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
            gap: "8px", // Compact gap between items
            justifyContent: "center",
          }}
        >
          {racks.map((rack, index) => (
            <div
              key={index}
              style={{
                border: "1px solid #007bff",
                borderRadius: "6px",
                backgroundColor:
                  rack.rack_id !== "Empty Rack"
                    ? highlightedRackIndex === index
                      ? "#DFF6FF"
                      : "#fff"
                    : highlightedRackIndex === index
                    ? "#DFF6FF"
                    : "#FF7F7F",
                boxShadow: "0 2px 6px rgba(0, 0, 0, 0.1)",
                transition: "transform 0.2s, background-color 0.2s",
                cursor: "pointer",
                padding: "5px",
                textAlign: "center",
                fontSize: "12px",
                fontWeight: "500",
                color: rack.rack_id === "Empty Rack" ? "#999" : "#333",
                height: "80px",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                position: "relative",
                overflow: "hidden",
                // border: "1px solid blue",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "scale(1.02)";
                e.currentTarget.style.boxShadow =
                  "0 4px 10px rgba(0, 0, 0, 0.15)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "scale(1)";
                e.currentTarget.style.boxShadow =
                  "0 2px 6px rgba(0, 0, 0, 0.1)";
              }}
            >
              <span
                style={{
                  position: "absolute",
                  top: "5px",
                  right: "5px",
                  fontSize: "10px",
                  color: "#666",
                }}
              >
                #{index + 1}
              </span>
              <div
                style={{
                  fontSize: "14px",
                  fontWeight: "bold",
                  padding: "2px 4px",
                  borderRadius: "4px",
                  color: "#333",
                  textShadow: "0.5px 0.5px 0 rgba(0, 0, 0, 0.1)",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "4px", // Space between items
                }}
              >
                <>
                  <div>
                    {highlightedRackIndex !== last
                      ? rack.rack_id
                      : highlightedRackIndex == index
                      ? newWrackId === ""
                        ? "..."
                        : newWrackId
                      : rack.rack_id}
                  </div>
                </>
                <>
                  <div>
                    (
                    {highlightedRackIndex !== last
                      ? rack.KIT_ID || "N/A"
                      : highlightedRackIndex == index
                      ? kitId === ""
                        ? "..."
                        : `KT-${kitId}`
                      : rack.KIT_ID || "N/A"}
                    )
                  </div>
                </>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
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
    console.log(colorValue);

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

  // -------------END of SCHEDULES----------------

  const [selectedValue, setSelectedValue] = useState("");

  const options = [
    { value: "", label: "Select an option" },
    { value: "STATION", label: "STATION" },
    { value: "RACK", label: "RACK" },
    { value: "SCHEDULE", label: "SCHEDULE" },
  ];

  const handleChange = (e) => {
    setSelectedValue(e.target.value);
    setHighlightedGroupIndex(null);
    setFocusState(null);

    setHighlightedRackIndex(null);

    setFocusRackState(null);
  };

  // ---------------END of Options

  const [highlightedRackIndexForSCH, setHighlightedRackIndexForSCH] =
    useState(null);
  const [highlightedBinIndexForSCH, setHighlightedBinIndexForSCH] =
    useState(null);

  const AnimatedSchedules = ({
    highlightedRackIndexForSCH,
    highlightedBinIndexForSCH,
    group,
  }) => {
    // let group =

    return (
      <div
        className="container"
        style={{
          maxWidth: "100%",
          padding: "10px",
          border: "1px solid",
          height: "100%",
          borderRadius: "10px",
          boxShadow: "0 4px 8px rgba(0, 0, 0, 0.2)",
        }}
      >
        <h2
          style={{
            textAlign: "center",
            marginBottom: "20px",
            color: "#007bff",
            fontWeight: "bold",
          }}
        >
          Bin Overview
        </h2>
        <h3
          style={{ textAlign: "center", marginBottom: "20px", color: "#333" }}
        >
          {group.Group_id}
        </h3>
        <div
          className="group-tables"
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            flexDirection: "row",
            // overflowX: "auto",
          }}
        >
          {group.racks &&
            group.racks.map((rack, index) => (
              <table
                className="single-column-table"
                key={rack.rack_id}
                style={{
                  borderCollapse: "collapse",
                  boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)",
                  borderRadius: "8px",
                  overflow: "hidden",
                  padding: "10px",
                  width: "auto",
                  backgroundColor:
                    highlightedRackIndexForSCH === index ? "#ADD8E6" : "white",
                  margin: "2px",
                  fontSize: "13px",
                  // border: "1px",
                }}
              >
                <thead>
                  <tr>
                    <th
                      style={{
                        backgroundColor: "#f0f0f0",
                        color: "#555",
                        padding: "4px",
                        textAlign: "center",
                        borderBottom: "2px solid #ccc",
                      }}
                    >
                      {rack.rack_id}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {rack.bins.map((bin, rowIndex) => (
                    <tr
                      key={rowIndex}
                      style={{
                        border:
                          highlightedRackIndexForSCH === index &&
                          highlightedBinIndexForSCH === rowIndex
                            ? "4px solid black"
                            : "1px solid grey",
                      }}
                    >
                      <td
                        style={{
                          backgroundColor:
                            highlightedRackIndexForSCH === index &&
                            highlightedBinIndexForSCH === rowIndex
                              ? selectedColor === ""
                                ? "grey"
                                : `rgb(${selectedColor})`
                              : "gray",
                          padding: "4px",
                          textAlign: "center",
                          border: "1px solid #ddd",
                          fontWeight: "bold",
                          transition: "background-color 0.3s",
                        }}
                      >
                        <p style={{ margin: "0", padding: "0" }}>
                          {bin.bin_id}
                        </p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ))}
        </div>
      </div>
    );
  };

  return (
    <Container className="setup">
      <h1>Setup</h1>

      <div className="container mt-5">
        <div className="form-group">
          <label
            htmlFor="awesomeSelect"
            className="h4 text-dark font-weight-bold mb-3"
          >
            Choose an Option to Add
          </label>
          <select
            id="awesomeSelect"
            className="form-select form-select-lg mb-3 shadow-sm border-1 rounded-3 px-4 py-2"
            value={selectedValue}
            onChange={handleChange}
            aria-label="Select an Option"
          >
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <ToastContainer />
      <Row>
        {selectedValue === "STATION" && (
          <Row md={3}>
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
                      onFocus={handleInputFocus} // Trigger highlighting on focus
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
                    style={{
                      maxHeight: `${groups.length}00px`,
                      overflowY: "auto",
                    }}
                  >
                    {groups.map((group, index) => (
                      <div
                        key={index}
                        className="d-flex justify-content-between align-items-center mb-2"
                        onMouseEnter={() => handleMouseEnter(index)}
                        onMouseLeave={handleMouseLeave}
                        style={{ cursor: "pointer" }}
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

            <style jsx="true">
              {`
                .group-box {
                  transition: background-color 0.3s ease;
                }

                .highlighted {
                  background-color: #e0f7fa;
                  border: 2px solid #007bff;
                }

                .group-box:hover {
                  background-color: #f0f8ff;
                }
              `}
            </style>
            <AnimatedGroup
              groups={groups}
              newGroupId={newGroupId}
              setNewGroupId={setNewGroupId}
              handleAddGroup={handleAddGroup}
              errors={errors}
              highlightedIndex={highlightedGroupIndex}
            />
          </Row>
        )}

        {selectedValue === "RACK" && (
          <Row md={2}>
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
                      onChange={(selectedOption) => {
                        setGroupIdForWrack(
                          selectedOption ? selectedOption.value : ""
                        );

                        setFocusRackState(null);
                        setHighlightedRackIndex(null);
                      }}
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
                          <div
                            key={index}
                            style={{ marginBottom: "10px", cursor: "pointer" }}
                          >
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
                                  onMouseEnter={() =>
                                    handleMouseEnterRack(rackIndex)
                                  }
                                  onMouseLeave={handleMouseLeaveRack}
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
                                  {rackIndex !== 0 && (
                                    <Button
                                      variant="danger"
                                      size="sm"
                                      onClick={() => handleDeleteRack(rack)}
                                      style={{ borderRadius: "5px" }}
                                    >
                                      Delete
                                    </Button>
                                  )}
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
                      onFocus={handleRackInputFocus}
                      placeholder="Enter new rack ID"
                    />
                  </Form.Group>

                  {/* Input for KIT_ID */}
                  <Form.Group controlId="kitId" style={{ marginTop: "20px" }}>
                    <Form.Label>KIT NO</Form.Label>
                    <Form.Control
                      type="number"
                      value={kitId}
                      min={0}
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
            {groupIdForWrack && (
              <AnimatedRacks
                highlightedRackIndex={highlightedRackIndex}
                groupIdForWrack={groupIdForWrack}
                group={data.find((group) => group.Group_id === groupIdForWrack)}
                newWrackId={newWrackId}
              />
            )}
          </Row>
        )}

        {selectedValue === "SCHEDULE" && (
          <Row md={2}>
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
                      onChange={(selectedOption) => {
                        setWrackIdForSchedule(
                          selectedOption ? selectedOption.value : ""
                        );

                        let group = data.find(
                          (group) => group.Group_id === groupIdForSchedule
                        );

                        setHighlightedRackIndexForSCH(
                          selectedOption && group.racks
                            ? group.racks.findIndex(
                                (rack) => rack.rack_id === selectedOption.value
                              )
                            : null
                        );
                      }}
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
                      onChange={(selectedOption) => {
                        setBinIdForSchedule(
                          selectedOption ? selectedOption.value : ""
                        );

                        function getLastCharAsNumber(str) {
                          if (str.length === 0) {
                            return NaN; // Return NaN for an empty string
                          }
                          const lastChar = str.charAt(str.length - 1);
                          return Number(lastChar) - 1;
                        }

                        setHighlightedBinIndexForSCH(
                          selectedOption
                            ? getLastCharAsNumber(selectedOption.value)
                            : null
                        );
                      }}
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

            {groupIdForSchedule && (
              <AnimatedSchedules
                highlightedBinIndexForSCH={highlightedBinIndexForSCH}
                highlightedRackIndexForSCH={highlightedRackIndexForSCH}
                group={data.find(
                  (group) => group.Group_id === groupIdForSchedule
                )}
              />
            )}
          </Row>
        )}
      </Row>
    </Container>
  );
};

export default Setup;
