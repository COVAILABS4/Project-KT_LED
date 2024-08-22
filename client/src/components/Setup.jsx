import React, { useState, useEffect } from "react";
import axios from "axios";
import { Form, Button, Card, Container, Row, Col } from "react-bootstrap";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./Setup.css";
import "react-tooltip/dist/react-tooltip.css";
import { Tooltip } from "react-tooltip";
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

const Setup = ({ fetchData, groups, racks, bins }) => {
  const [newGroupId, setNewGroupId] = useState("");
  const [newGroupDeviceId, setNewGroupDeviceId] = useState("");
  const [groupIdForWrack, setGroupIdForWrack] = useState("");
  const [newWrackId, setNewWrackId] = useState("");
  const [macAddress, setMacAddress] = useState("");
  const [groupIdForSchedule, setGroupIdForSchedule] = useState("");
  const [wrackIdForSchedule, setWrackIdForSchedule] = useState("");
  const [binIdForSchedule, setBinIdForSchedule] = useState("");
  const [scheduleTime, setScheduleTime] = useState("");
  const [selectedColor, setSelectedColor] = useState("");
  const [ipAddress, setIpAddress] = useState("");
  const [device_id, setDeviceID] = useState("");
  const [newIP, setNewIP] = useState("");
  const ip = window.location.hostname;

  console.log(groups);

  const handleGetIpAddress = () => {
    axios
      .get("http://" + ip + ":5000/address/getIP/" + device_id)
      .then((response) => {
        console.log(response.data.ip);
        setIpAddress(response.data.ip || "");
      })
      .catch((error) => notify("Failed to fetch IP address", "error"));
  };

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

  const handleAddGroup = () => {
    axios
      .post("http://" + ip + ":5000/new/group", {
        newGroupid: newGroupId,
        newGroupDeviceId: newGroupDeviceId,
      })
      .then((response) => {
        notify("Group added successfully!", "success");
        // setNewGroupId("");
      })
      .catch((error) => notify("Failed to add group", "error"));
  };

  const handleAddWrack = () => {
    axios
      .post("http://" + ip + ":5000/new/wrack", {
        Groupid: groupIdForWrack,
        newWrackid: newWrackId,
        id: macAddress,
      })
      .then((response) => {
        notify("Wrack added successfully!", "success");
        // setGroupIdForWrack("");
        // setNewWrackId("");
        // setMacAddress("");
      })
      .catch((error) => notify("Failed to add wrack", "error"));
  };

  const handleAddSchedule = () => {
    const newSchedule = {
      time: scheduleTime,
      enabled: true,
      color: selectedColor.split(",").map(Number),
    };
    axios
      .post("http://" + ip + ":5000/new/schedule", {
        group_id: groupIdForSchedule,
        wrack_id: wrackIdForSchedule,
        bin_id: binIdForSchedule,
        new_schduled: newSchedule,
      })
      .then((response) => {
        notify("Schedule added successfully!", "success");
        // setGroupIdForSchedule("");
        // setWrackIdForSchedule("");
        // setBinIdForSchedule("");
        // setScheduleTime("");
        // setSelectedColor("");
      })
      .catch((error) => notify("Failed to add schedule", "error"));
  };

  const handleColorSelect = (colorValue) => {
    setSelectedColor(colorValue);
  };

  const handleSetIpAddress = () => {
    axios
      .post("http://" + ip + ":5000/address/setIP", {
        ip: ipAddress,
        device_id: device_id,
      })
      .then((response) => {
        setNewIP(ipAddress);
        // setIpAddress("");
        notify("IP address set successfully!", "success");
      })
      .catch((error) => notify("Failed to set IP address", "error"));
  };

  const handleDeleteRack = (rack) => {
    axios
      .post("http://" + ip + ":5000/delete/rack", {
        Groupid: groupIdForWrack,
        rackId: rack,
      })
      .then((response) => {
        notify("Rack deleted successfully!", "success");
        // Refresh or re-fetch racks here if needed
      })
      .catch((error) => notify("Failed to delete rack", "error"));
  };

  return (
    <Container className="setup">
      <h1>Setup</h1>
      <ToastContainer />
      <Row>
        <Col md={4}>
          <Card className="setup-card">
            <Card.Body>
              <Card.Title>Set IP Address</Card.Title>
              <Form>
                <Form.Group controlId="ipAddress">
                  <Form.Label>Device ID</Form.Label>
                  <Form.Control
                    type="text"
                    value={device_id || ""}
                    onChange={(e) => setDeviceID(e.target.value)}
                  />

                  <Form.Label>IP Address</Form.Label>
                  <Form.Control
                    type="text"
                    value={ipAddress || ""}
                    onChange={(e) => setIpAddress(e.target.value)}
                  />
                </Form.Group>

                <Button
                  variant="primary"
                  onClick={handleGetIpAddress}
                  style={{
                    margin: "5px",
                    padding: "10px 20px",
                    backgroundColor: "#007bff",
                    borderColor: "#007bff",
                    borderRadius: "5px",
                    fontSize: "16px",
                  }}
                >
                  Get IP Address
                </Button>
                <Button
                  variant="primary"
                  onClick={handleSetIpAddress}
                  style={{
                    margin: "5px",
                    padding: "10px 20px",
                    backgroundColor: "#007bff",
                    borderColor: "#007bff",
                    borderRadius: "5px",
                    fontSize: "16px",
                  }}
                >
                  Set IP Address
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="setup-card">
            <Card.Body>
              <Card.Title>Add Group</Card.Title>
              <Form>
                <Form.Group controlId="newGroupId">
                  <Form.Label>New Group ID</Form.Label>
                  <Form.Control
                    type="text"
                    value={newGroupId || ""}
                    onChange={(e) => setNewGroupId(e.target.value)}
                  />

                  <Form.Label>New Group Device ID</Form.Label>
                  <Form.Control
                    type="text"
                    value={newGroupDeviceId || ""}
                    onChange={(e) => setNewGroupDeviceId(e.target.value)}
                  />
                </Form.Group>
                <Button variant="primary" onClick={handleAddGroup}>
                  Add Group
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
                Add Rack
              </Card.Title>
              <Form>
                {/* Dropdown for selecting Group ID */}
                <Form.Group controlId="groupIdForWrack">
                  <Form.Label>Group ID</Form.Label>
                  <Form.Control
                    as="select"
                    value={groupIdForWrack || ""}
                    onChange={(e) => setGroupIdForWrack(e.target.value)}
                  >
                    <option value="">Select Group</option>
                    {groups.map((group, index) => (
                      <option key={index} value={group}>
                        {group}
                      </option>
                    ))}
                  </Form.Control>
                </Form.Group>

                {/* Display existing racks for the selected group */}
                {groupIdForWrack && (
                  <div
                    className="existing-racks"
                    style={{
                      marginTop: "20px",
                      maxHeight: "150px",
                      overflowY: "auto",
                    }}
                  >
                    <h5 style={{ color: "#343a40" }}>
                      Existing Racks in {groupIdForWrack}:
                    </h5>
                    {racks
                      .filter((rack) => rack.group_id === groupIdForWrack)
                      .map((rackItem, index) => (
                        <div key={index} style={{ marginBottom: "10px" }}>
                          {rackItem.racks.map((rack, rackIndex) => (
                            <div
                              key={rackIndex}
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                                padding: "5px",
                                backgroundColor:
                                  rackIndex === 0 ? "#e9f7f5" : "transparent",
                                borderRadius: "5px",
                                border:
                                  rackIndex === 0
                                    ? "1px solid #007bff"
                                    : "none",
                              }}
                            >
                              <p
                                style={{
                                  margin: 0,
                                  fontWeight:
                                    rackIndex === 0 ? "bold" : "normal",
                                  color:
                                    rackIndex === 0 ? "#007bff" : "#343a40",
                                }}
                              >
                                {rackIndex + 1} : {" " + rack}
                                {"  "}
                                {rackIndex === 0 && "(master)"}
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
                          ))}
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
                    value={newWrackId || ""}
                    onChange={(e) => setNewWrackId(e.target.value)}
                  />
                </Form.Group>

                {/* Input for MAC Address / Device ID */}
                <Form.Group
                  controlId="macAddress"
                  style={{ marginTop: "10px" }}
                >
                  <Form.Label>Device ID</Form.Label>
                  <Form.Control
                    type="text"
                    value={macAddress || ""}
                    onChange={(e) => setMacAddress(e.target.value)}
                  />
                </Form.Group>

                {/* Button to Add Rack */}
                <Button
                  variant="primary"
                  onClick={handleAddWrack}
                  style={{
                    marginTop: "20px",
                    width: "100%",
                    borderRadius: "5px",
                  }}
                >
                  Add Rack
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>

        <Col md={4}>
          <Card className="setup-card">
            <Card.Body>
              <Card.Title>Add Schedule</Card.Title>
              <Form>
                <Form.Group controlId="groupIdForSchedule">
                  <Form.Label>Group ID</Form.Label>
                  <Form.Control
                    type="text"
                    value={groupIdForSchedule || ""}
                    onChange={(e) => setGroupIdForSchedule(e.target.value)}
                  />
                </Form.Group>
                <Form.Group controlId="wrackIdForSchedule">
                  <Form.Label>Wrack ID</Form.Label>
                  <Form.Control
                    type="text"
                    value={wrackIdForSchedule || ""}
                    onChange={(e) => setWrackIdForSchedule(e.target.value)}
                  />
                </Form.Group>
                <Form.Group controlId="binIdForSchedule">
                  <Form.Label>Bin ID</Form.Label>
                  <Form.Control
                    type="text"
                    value={binIdForSchedule || ""}
                    onChange={(e) => setBinIdForSchedule(e.target.value)}
                  />
                </Form.Group>
                <Form.Group controlId="scheduleTime">
                  <Form.Label>Schedule Time</Form.Label>
                  <Form.Control
                    type="time"
                    value={scheduleTime || ""}
                    onChange={(e) => setScheduleTime(e.target.value)}
                  />
                </Form.Group>
                <Form.Group controlId="color">
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
                        {/* This is where the tooltip is referenced by its ID */}
                        <Tooltip id={`tooltip-${index}`} />
                      </div>
                    ))}
                  </div>
                </Form.Group>

                <Button variant="primary" onClick={handleAddSchedule}>
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
