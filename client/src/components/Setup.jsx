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
  const [newGroupDeviceId, setNewGroupDeviceId] = useState("");
  const [errors, setErrors] = useState({});

  const deviceOptions = forSetIP.map((device) => ({
    value: device.ID,
    label: device.ID,
  }));

  const validateForm = () => {
    const newErrors = {};
    if (!newGroupId) newErrors.newGroupId = "Group ID is required.";
    if (!newGroupDeviceId)
      newErrors.newGroupDeviceId = "Device ID is required.";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleAddGroup = () => {
    if (!validateForm()) return;

    axios
      .post("http://" + ip + ":5000/new/group", {
        newGroupid: newGroupId,
        newGroupDeviceId: newGroupDeviceId.value,
      })
      .then((response) => {
        notify("Stack added successfully!", "success");
        setNewGroupId("");
        setNewGroupDeviceId("");
        setErrors({}); // Clear errors upon successful addition
      })
      .catch((error) => notify("Failed to add Stack", "error"));
  };

  const handleDeleteGroup = async (groupId) => {
    try {
      await axios.post("http://" + ip + ":5000/delete/group", { groupId });
      notify("Stack deleted successfully!", "success");
    } catch (error) {
      notify("Failed to delete group", "error");
    }
  };

  //-------------------------END of GROUP----------------------------------------------//

  //For setup IP
  const [ipAddress, setIpAddress] = useState("");
  const [groupIdForSetIp, setGroupIdForSetIp] = useState("");
  const [errors1, setErrors1] = useState({});

  const options = AllStaticDevices.map((device) => ({
    value: device.master_id,
    label: device.master_id,
  }));

  const handleSelectChange = (selectedOption) => {
    setGroupIdForSetIp(selectedOption ? selectedOption.value : "");
    if (selectedOption) {
      setErrors((prevErrors) => ({ ...prevErrors, groupIdForSetIp: "" }));
    }
  };

  const validateForm1 = () => {
    const newErrors = {};
    if (!groupIdForSetIp) newErrors.groupIdForSetIp = "Group ID is required.";
    if (!ipAddress) newErrors.ipAddress = "IP Address is required.";
    setErrors1(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleGetIpAddress = () => {
    if (!groupIdForSetIp) {
      setErrors({ groupIdForSetIp: "Please select a Group ID." });
      return;
    }

    axios
      .get("http://" + ip + ":5000/address/getIP/" + groupIdForSetIp)
      .then((response) => {
        setIpAddress(response.data.ip || "");
        setErrors({});
        notify("IP address fetched successfully!", "success");
      })
      .catch((error) => notify("Failed to fetch IP address", "error"));
  };

  const handleSetIpAddress = () => {
    if (!validateForm1()) return;

    axios
      .post("http://" + ip + ":5000/address/setIP", {
        ip: ipAddress,
        group_id: groupIdForSetIp,
      })
      .then((response) => {
        notify("IP address set successfully!", "success");
        setIpAddress("");
        setGroupIdForSetIp("");
      })
      .catch((error) => notify("Failed to set IP address", "error"));
  };

  //-------------------------END  of SETUP IP-----------------------------------------//
  //For Add Rack
  const [groupIdForWrack, setGroupIdForWrack] = useState("");
  const [newWrackId, setNewWrackId] = useState("");
  const [deviceId4rack, setDeviceId4rack] = useState("");

  const deviceOptions1 = slaveDevices.map((device) => ({
    value: device.ID,
    label: device.ID,
  }));

  const groupOptions = groups.map((group) => ({
    value: group.group_id,
    label: group.group_id,
  }));

  useEffect(() => {
    if (groupIdForWrack) {
      const filteredRacks = racks.filter(
        (rack) => rack.group_id === groupIdForWrack
      );

      if (filteredRacks.length === 0 || filteredRacks[0].racks.length === 0) {
        let local_masterid = "";

        AllStaticDevices.forEach((element) => {
          if (element.master_id === groupIdForWrack) {
            local_masterid = element.ID;
          }
        });

        // Set mac address once, when the group has no racks
        setDeviceId4rack(local_masterid);
      }
    }
  }, [groupIdForWrack, racks, AllStaticDevices]);

  const handleAddWrack = () => {
    if (!groupIdForWrack || !newWrackId || !deviceId4rack) {
      notify("Please fill in all fields before adding a rack.", "warning");
      return;
    }

    axios
      .post("http://" + ip + ":5000/new/wrack", {
        Groupid: groupIdForWrack,
        newWrackid: newWrackId,
        id: deviceId4rack,
      })
      .then((response) => {
        notify("rack added successfully!", "success");
        // Reset form fields after successful addition
        setNewWrackId("");
        setDeviceId4rack("");
      })
      .catch((error) => {
        console.error("Error adding rack:", error);
        notify("Failed to add rack", "error");
      });
  };

  const handleDeleteRack = (rack) => {
    axios
      .post("http://" + ip + ":5000/delete/rack", {
        Groupid: groupIdForWrack,
        rackId: rack.rack_id,
      })
      .then((response) => {
        notify("Rack deleted successfully!", "success");
        // Refresh or re-fetch racks here if needed
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
                Add Stack
              </Card.Title>
              <Form>
                <Form.Group controlId="newGroupId">
                  <Form.Label>New Stack Name</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Enter Stack Name"
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
                <Form.Group controlId="newGroupDeviceId">
                  <Form.Label>New Stack's Device ID</Form.Label>
                  <Select
                    options={deviceOptions}
                    value={newGroupDeviceId}
                    onChange={setNewGroupDeviceId}
                    isSearchable={true}
                    isClearable
                    placeholder="Select Device ID"
                    maxMenuHeight={160}
                    noOptionsMessage={() => "No Devices"}
                  />
                  {errors.newGroupDeviceId && (
                    <Alert variant="danger" className="mt-2">
                      {errors.newGroupDeviceId}
                    </Alert>
                  )}
                </Form.Group>
                <Button
                  className="w-100 mt-3"
                  variant="primary"
                  onClick={handleAddGroup}
                  disabled={!newGroupId || !newGroupDeviceId}
                >
                  Add
                </Button>
              </Form>

              {/* Division for Existing Groups */}
              {groups.length !== 0 && (
                <Card.Title className="mt-4">Existing Stacks</Card.Title>
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
                        {index + 1}: {group.group_id} ({group.device_id})
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
                Setup IP Address
              </Card.Title>

              <Form>
                <Form.Group controlId="groupSelect">
                  <Form.Label>Stack Name</Form.Label>
                  <Select
                    value={options.find(
                      (option) => option.value === groupIdForSetIp
                    )}
                    onChange={handleSelectChange}
                    options={options}
                    isSearchable
                    isClearable
                    maxMenuHeight={150}
                    isMulti={false}
                    placeholder="Select Stack"
                    noOptionsMessage={() => "No Stacks"}
                  />
                  {errors1.groupIdForSetIp && (
                    <Alert variant="danger" className="mt-2">
                      {errors1.groupIdForSetIp}
                    </Alert>
                  )}
                </Form.Group>

                <Form.Group controlId="ipAddress">
                  <Form.Label>IP Address</Form.Label>
                  <Form.Control
                    type="text"
                    value={ipAddress}
                    placeholder="Enter IP Address"
                    onChange={(e) => setIpAddress(e.target.value)}
                    isInvalid={!!errors1.ipAddress}
                  />
                  {errors1.ipAddress && (
                    <Form.Control.Feedback type="invalid">
                      {errors1.ipAddress}
                    </Form.Control.Feedback>
                  )}
                </Form.Group>

                <div className="d-flex justify-content-around">
                  <Button
                    variant="primary"
                    onClick={handleGetIpAddress}
                    className="mr-2"
                    disabled={!groupIdForSetIp}
                  >
                    Get IP Address
                  </Button>
                  <Button
                    variant="primary"
                    onClick={handleSetIpAddress}
                    disabled={!groupIdForSetIp || !ipAddress}
                  >
                    Set IP Address
                  </Button>
                </div>
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
                {/* Dropdown for selecting Group ID using react-select */}
                <Form.Group controlId="groupIdForWrack">
                  <Form.Label>Stack Name</Form.Label>
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
                    placeholder="Select Stack"
                    noOptionsMessage={() => "No Stack"}
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
                                {rackIndex + 1} : {" " + rack.rack_id}(
                                {rack.device_id}){"  "}
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
                    value={newWrackId}
                    onChange={(e) => setNewWrackId(e.target.value)}
                    placeholder="Enter new rack ID"
                  />
                </Form.Group>

                {/* Dropdown for selecting available Device ID using react-select */}
                <Form.Group
                  controlId="deviceId4rack"
                  style={{ marginTop: "10px" }}
                >
                  {groupIdForWrack && <Form.Label>Device ID</Form.Label>}

                  {groupIdForWrack &&
                    (() => {
                      const filteredRacks = racks.filter(
                        (rack) => rack.group_id === groupIdForWrack
                      );

                      if (
                        filteredRacks.length > 0 &&
                        filteredRacks[0].racks.length > 0
                      ) {
                        return (
                          <Select
                            options={deviceOptions1}
                            value={deviceOptions1.find(
                              (option) => option.value === deviceId4rack
                            )}
                            onChange={(selectedOption) =>
                              setDeviceId4rack(
                                selectedOption ? selectedOption.value : ""
                              )
                            }
                            isSearchable={true}
                            isClearable
                            placeholder="Select Device ID"
                            maxMenuHeight={160}
                            noOptionsMessage={() => "No Devices"}
                          />
                        );
                      } else {
                        let local_masterid = "";

                        AllStaticDevices.forEach((element) => {
                          if (element.master_id === groupIdForWrack)
                            local_masterid = element.ID;
                        });

                        return (
                          <Select
                            options={[
                              {
                                label: local_masterid,
                                value: local_masterid,
                              },
                            ]}
                            value={{
                              label: local_masterid,
                              value: local_masterid,
                            }}
                            isDisabled={true}
                            placeholder="Select Device ID"
                            maxMenuHeight={160}
                          />
                        );
                      }
                    })()}
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
                  disabled={!newWrackId || !deviceId4rack}
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
                  <Form.Label>Stack Name</Form.Label>
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
                    placeholder="Select Stack"
                    noOptionsMessage={() => "No Stacks"}
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
