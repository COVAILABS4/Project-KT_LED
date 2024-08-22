import React, { useState, useEffect } from "react";
import axios from "axios";
import { Form, Button, Card, Container, Row, Col } from "react-bootstrap";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./Setup.css";
import "react-tooltip/dist/react-tooltip.css";
import { Tooltip } from "react-tooltip";

import Select from "react-select";
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
}) => {
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

  const deviceOptions = availableStaticDevices.map((device) => ({
    value: device.ID,
    label: device.ID,
  }));

  const deviceOptions1 = availableDevices.map((device) => ({
    value: device.ID,
    label: device.ID,
  }));

  const ip = window.location.hostname;
  // console.log(availableDevices);

  const handleGetIpAddress = () => {
    axios
      .get("http://" + ip + ":5000/address/getIP/" + device_id)
      .then((response) => {
        // console.log(response.data.ip);
        setIpAddress(response.data.ip || "");
      })
      .catch((error) => notify("Failed to fetch IP address", "error"));
  };
  const handleAddIpAddress = () => {
    axios
      .post("http://" + ip + ":5000/address/addIP", {
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
        newGroupDeviceId: newGroupDeviceId.value,
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
        bin_id: wrackIdForSchedule + binIdForSchedule,
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

  const handleDeleteGroup = async (groupId) => {
    try {
      await axios.post("http://" + ip + ":5000/delete/group", { groupId });
      notify("Group deleted successfully!", "success");
    } catch (error) {
      notify("Failed to delete group", "error");
    }
  };

  const groupOptions = groups.map((group) => ({
    value: group,
    label: group,
  }));

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

  const handleSelectChange = (selectedOption) => {
    setDeviceID(selectedOption ? selectedOption.value : "");
  };

  const [isAddingNew, setIsAddingNew] = useState(false);

  const dropdownData = !isAddingNew ? availableStaticDevices : availableDevices;

  const handleToggle = () => {
    setIsAddingNew(!isAddingNew);
  };

  const options = dropdownData.map((device) => ({
    value: device.ID,
    label: device.ID,
  }));
  return (
    <Container className="setup">
      <h1>Setup</h1>
      <ToastContainer />
      <Row>
        <Col md={4}>
          <Card className="setup-card">
            <Card.Body>
              <Card.Title>Setup IP Address</Card.Title>
              <Form.Check
                type="switch"
                id="custom-switch"
                label={
                  isAddingNew
                    ? "Adding New Device"
                    : "Get or Set Existing Device"
                }
                checked={isAddingNew}
                onChange={handleToggle}
                style={{ margin: "15px 0" }}
              />
              <Form>
                <Form.Group controlId="deviceSelect">
                  <Form.Label>Device ID</Form.Label>
                  <Select
                    value={options.find((option) => option.value === device_id)}
                    onChange={handleSelectChange}
                    options={options}
                    isSearchable
                    isClearable
                    maxMenuHeight={150}
                    isMulti={false}
                    placeholder="Select Device"
                  />

                  <Form.Label>IP Address</Form.Label>
                  <Form.Control
                    type="text"
                    value={ipAddress || ""}
                    placeholder="Enter IP Address"
                    onChange={(e) => setIpAddress(e.target.value)}
                  />
                </Form.Group>

                {!isAddingNew ? (
                  <div>
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
                  </div>
                ) : (
                  <Button
                    variant="primary"
                    onClick={handleAddIpAddress}
                    style={{
                      margin: "5px",
                      padding: "10px 20px",
                      backgroundColor: "#007bff",
                      borderColor: "#007bff",
                      borderRadius: "5px",
                      fontSize: "16px",
                    }}
                  >
                    Add
                  </Button>
                )}
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
                    placeholder="Enter Group ID"
                    value={newGroupId || ""}
                    onChange={(e) => setNewGroupId(e.target.value)}
                  />
                </Form.Group>
                <Form.Group controlId="newGroupDeviceId">
                  <Form.Label>New Group Device ID</Form.Label>
                  <Select
                    options={deviceOptions}
                    value={newGroupDeviceId}
                    onChange={setNewGroupDeviceId}
                    isSearchable={true}
                    isClearable
                    placeholder="Select Device ID"
                    maxMenuHeight={160}
                  />
                </Form.Group>
                <Button
                  style={{
                    width: "100%",
                    marginTop: "15px",
                  }}
                  variant="primary"
                  onClick={handleAddGroup}
                >
                  Add
                </Button>
              </Form>

              {/* Division for Existing Groups */}
              {groups.length != 0 && (
                <Card.Title style={{ marginTop: "20px" }}>
                  Existing Groups
                </Card.Title>
              )}
              {groups && (
                <div
                  className="existing-groups"
                  style={{
                    marginTop: "20px",
                    maxHeight: "150px",
                    overflowY: "auto",
                  }}
                >
                  {groups.map((group, index) => (
                    <div key={index} style={{ marginBottom: "10px" }}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          padding: "5px",
                          backgroundColor: "transparent",
                          borderRadius: "5px",
                          border: "none",
                        }}
                      >
                        <p
                          style={{
                            margin: 0,
                            fontWeight: "normal",
                            color: "#343a40",
                          }}
                        >
                          {index + 1} {" : " + group}
                        </p>
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => handleDeleteGroup(group)}
                          style={{ borderRadius: "5px" }}
                        >
                          Delete
                        </Button>
                      </div>
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
                {/* Dropdown for selecting Group ID using react-select */}
                <Form.Group controlId="groupIdForWrack">
                  <Form.Label>Group ID</Form.Label>
                  <Select
                    options={groupOptions}
                    value={groupOptions.find(
                      (option) => option.value === groupIdForWrack
                    )}
                    onChange={(selectedOption) =>
                      setGroupIdForWrack(selectedOption.value)
                    }
                    isSearchable={true}
                    isClearable
                    placeholder="Select Group"
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
                    }}
                  >
                    <h5 style={{ color: "#343a40" }}>
                      {(() => {
                        const filteredRacks = racks.filter(
                          (rack) => rack.group_id === groupIdForWrack
                        );

                        // Check if the filtered result contains any racks
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

                {/* Dropdown for selecting available Device ID using react-select */}
                <Form.Group
                  controlId="macAddress"
                  style={{ marginTop: "10px" }}
                >
                  <Form.Label>Device ID</Form.Label>
                  <Select
                    options={(() => {
                      const filteredRacks = racks.filter(
                        (rack) => rack.group_id === groupIdForWrack
                      );

                      // Check if the filtered result contains any racks
                      if (
                        filteredRacks.length > 0 &&
                        filteredRacks[0].racks.length > 0
                      ) {
                        return deviceOptions1;
                      } else {
                        return availableStaticDevices;
                      }
                    })()}
                    value={deviceOptions1.find(
                      (option) => option.value === macAddress
                    )}
                    onChange={(selectedOption) =>
                      setMacAddress(selectedOption.value)
                    }
                    isSearchable={true}
                    isClearable
                    placeholder="Select Device ID"
                    maxMenuHeight={160}
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
                {/* Dropdown for selecting Group ID */}
                <Form.Group controlId="groupIdForSchedule">
                  <Form.Label>Group ID</Form.Label>
                  <Form.Control
                    as="select"
                    value={groupIdForSchedule || ""}
                    onChange={(e) => setGroupIdForSchedule(e.target.value)}
                  >
                    <option value="">Select Group</option>
                    {groups.map((group, index) => (
                      <option key={index} value={group}>
                        {group}
                      </option>
                    ))}
                  </Form.Control>
                </Form.Group>

                {/* Dropdown for selecting Rack ID */}
                <Form.Group controlId="wrackIdForSchedule">
                  <Form.Label>Rack ID</Form.Label>
                  <Form.Control
                    as="select"
                    value={wrackIdForSchedule || ""}
                    onChange={(e) => setWrackIdForSchedule(e.target.value)}
                  >
                    <option value="">Select Rack</option>
                    {racks
                      .filter((rack) => rack.group_id === groupIdForSchedule)
                      .map((rack, rackIndex) => {
                        return rack.racks.map((id, idIndex) => (
                          <option key={`${rackIndex}-${idIndex}`} value={id}>
                            {id}
                          </option>
                        ));
                      })}
                  </Form.Control>
                </Form.Group>

                {/* Dropdown for selecting Bin ID */}
                <Form.Group controlId="binIdForSchedule">
                  <Form.Label>Bin ID</Form.Label>
                  <Form.Control
                    as="select"
                    value={binIdForSchedule || ""}
                    onChange={(e) => setBinIdForSchedule(e.target.value)}
                  >
                    <option value="">Select Bin</option>
                    {["_01", "_02", "_03", "_04"].map((num, index) => {
                      return (
                        <option key={index} value={`${num}`}>
                          {`${wrackIdForSchedule}${num}`}
                        </option>
                      );
                    })}
                  </Form.Control>
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
