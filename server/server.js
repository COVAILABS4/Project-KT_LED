const express = require("express");
const cors = require("cors");
const fs = require("fs");
const xlsx = require("xlsx");
const multer = require("multer");
const axios = require("axios");
const path = require("path");
const { log } = require("util");
const app = express();
const port = 5000;

app.use(cors());
app.use(express.json());

const upload = multer({ dest: "uploads/" });

// Global cache
let cache = null;
let lastModified = 0;

// Function to update cache
const updateCache = () => {
  try {
    const stats = fs.statSync("./data.json");
    if (stats.mtimeMs !== lastModified) {
      const fileContent = fs.readFileSync("./data.json", "utf8");
      if (!fileContent.trim()) {
        console.error("data.json is empty.");
        cache = [];
      } else {
        cache = JSON.parse(fileContent);
      }
      lastModified = stats.mtimeMs;
    }
  } catch (error) {
    console.error("Error updating cache:", error);
    throw new Error("Error updating cache");
  }
};

// Utility function to save JSON file
const saveDataToFile = (data) => {
  try {
    fs.writeFileSync("./data.json", JSON.stringify(data, null, 2), "utf8");
    updateCache(); // Update cache after saving
  } catch (error) {
    console.error("Error writing data.json:", error);
    throw new Error("Error writing data.json");
  }
};

// Read users from Excel
const readUsersFromExcel = () => {
  const workbook = xlsx.readFile("user.xlsx");
  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  const users = xlsx.utils.sheet_to_json(sheet);
  return users;
};

const readStaticIP = (device_id) => {
  try {
    const fileContent = fs.readFileSync("./static.json", "utf8");
    const data = JSON.parse(fileContent);

    let ip = "";

    for (let index = 0; index < data.length; index++) {
      if (data[index].ID == device_id) {
        ip = data[index].IP;
        break;
      }
    }

    return ip;
  } catch (error) {
    console.error("Error reading static.json:", error);
    throw new Error("Error reading static.json");
  }
};

app.get("/device", (req, res) => {
  const filePath = path.join(__dirname, "static.json");

  fs.readFile(filePath, "utf8", (err, data) => {
    if (err) {
      console.error("Error reading file:", err);
      return res.status(500).json({ error: "Failed to read file" });
    }

    try {
      const jsonData = JSON.parse(data);
      res.json(jsonData);
    } catch (parseError) {
      console.error("Error parsing JSON:", parseError);
      res.status(500).json({ error: "Failed to parse JSON" });
    }
  });
});

app.get("/device/excel", (req, res) => {
  const workbook = xlsx.readFile("led_mac_data.xlsx"); // Replace with the actual file path
  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  const data = xlsx.utils.sheet_to_json(sheet);
  // console.log(data);

  // Extract only ID and isMaster fields
  const extractedData = data.map((row) => ({
    ID: row.ID,
    isMaster: row.isMaster,
    available: row.availability,
  }));

  res.json(extractedData);
});

// Utility function to write static IP to static.json
const writeStaticIP = (newIP, id, operation) => {
  try {
    // Read the existing data from the file
    let data = [];
    if (fs.existsSync("./static.json")) {
      data = JSON.parse(fs.readFileSync("./static.json", "utf8"));
    }

    // Find the object with the matching ID
    const index = data.findIndex((item) => item.ID === id);
    var isNew = data[index].IP === "";
    if (index !== -1) {
      // Update the IP if the ID is found
      data[index].IP = newIP;
    } else {
      // Add a new object if the ID is not found
      data.push({ IP: newIP, ID: id, master_id: "" });
    }

    // Write the updated data back to the file
    fs.writeFileSync("./static.json", JSON.stringify(data, null, 2), "utf8");
    return isNew;
  } catch (error) {
    console.error("Error writing static.json:", error);
    throw new Error("Error writing static.json");
  }
};

app.get("/address/getIP/:group_id", (req, res) => {
  try {
    const { group_id } = req.params;

    console.log(group_id);
    var staticIP = readStaticIP(read_device(group_id));

    if (staticIP == "") res.status(404);
    console.log(staticIP);
    res.json({ ip: staticIP });
  } catch (error) {
    res.status(500).send("Error reading static IP");
  }
});

// API to update the static IP
app.post("/address/addIP", (req, res) => {
  var { ip, device_id } = req.body;
  try {
    writeStaticIP(ip, device_id, "add");

    res.json({ message: "Static IP updated successfully" });
  } catch (error) {
    res.status(500).send("Error updating static IP");
  }
});

const read_device = (group_id) => {
  try {
    const fileContent = fs.readFileSync("./static.json", "utf8");
    const data = JSON.parse(fileContent);

    let device_id = "";

    for (let index = 0; index < data.length; index++) {
      if (data[index].master_id == group_id) {
        device_id = data[index].ID;
        break;
      }
    }

    return device_id;
  } catch (error) {
    console.error("Error reading static.json:", error);
    throw new Error("Error reading static.json");
  }
};

app.post("/address/setIP", (req, res) => {
  var { group_id, ip } = req.body;
  try {
    let device_id = read_device(group_id);

    var isNew = writeStaticIP(ip, device_id, "set");
    console.log("Status :  ", isNew);

    if (isNew) {
      let fail = updateADDGroupESP(group_id, device_id);

      if (fail) {
        res.status(404).json({ error: "Failed to update the group in ESP" });
        return;
      }
    }

    // updateLedMacDataExcel(device_id);
    res.json({ message: "Static IP updated successfully" });
  } catch (error) {
    res.status(500).send("Error updating static IP");
  }
});

// Login route
app.post("/login", (req, res) => {
  const { email, password } = req.body;
  const users = readUsersFromExcel();

  const user = users.find((user) => user.Email === email);
  if (user && password === user.Password) {
    res.json({ success: true, user: { email: user.Email } });
  } else {
    res
      .status(401)
      .json({ success: false, message: "Invalid email or password" });
  }
});

// Click update route
app.post("/click/update", (req, res) => {
  console.log("clicked Called");
  const bin_details = req.body;
  console.log(bin_details);

  updateCache(); // Ensure cache is up-to-date

  let group = cache.find((group) => group.Group_id === bin_details.group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === bin_details.rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins[bin_details.bin_idx];
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  console.log(bin.clicked);
  bin.clicked = true;
  console.log(bin.clicked);

  saveDataToFile(cache);
  res.send("Data updated successfully");
});

// Get data route
app.get("/data", (req, res) => {
  try {
    updateCache(); // Ensure cache is up-to-date
    res.json(cache);
  } catch (error) {
    res.status(500).send("Error reading data.json");
  }
});

const updateSchedulesWithDelay = (scheduleDataArray) => {
  scheduleDataArray.forEach((scheduleData, index) => {
    updatePushScheduleESP(
      scheduleData.group_id,
      scheduleData.rack_id,
      scheduleData.bin_id,
      scheduleData.new_schedule_time,
      scheduleData.color,
      scheduleData.master_device_id
    );
  });
};

// Import route
app.post("/import", upload.single("file"), (req, res) => {
  console.log("Called");

  const file = req.file;
  const workbook = xlsx.readFile(file.path);
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];
  const jsonData = xlsx.utils.sheet_to_json(worksheet);

  console.log(jsonData, file);

  updateCache(); // Ensure cache is up-to-date

  const scheduleDataArray = [];
  let errors = [];

  jsonData.forEach((row) => {
    const { Group_id, rack_id, bin_id, scheduled_time, color } = row;
    const group = cache.find((group) => group.Group_id === Group_id);
    if (!group) {
      errors.push(`Group ${Group_id} not found`);
      return;
    }
    const rack = group.racks.find((rack) => rack.rack_id === rack_id);
    if (!rack) {
      errors.push(`Rack ${rack_id} not found in group ${Group_id}`);
      return;
    }
    const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
    if (!bin) {
      errors.push(`Bin ${bin_id} not found in rack ${rack_id}`);
      return;
    }

    const colorArr = color.split(",").map(Number);

    // Insert the schedule in ascending order based on time
    let inserted = false;
    for (let i = 0; i < bin.schedules.length; i++) {
      const existingTime = bin.schedules[i].time.split(":").map(Number);
      const newTime = scheduled_time.split(":").map(Number);

      if (
        newTime[0] < existingTime[0] ||
        (newTime[0] === existingTime[0] && newTime[1] < existingTime[1])
      ) {
        bin.schedules.splice(i, 0, {
          enabled: true,
          time: scheduled_time,
          color: colorArr,
        });
        inserted = true;
        break;
      }
    }

    // If not inserted, push to the end (means it is the latest time)
    if (!inserted) {
      bin.schedules.push({
        enabled: true,
        time: scheduled_time,
        color: colorArr,
      });
    }

    // Add schedule data to array for delayed processing
    scheduleDataArray.push({
      group_id: Group_id,
      rack_id: rack_id,
      bin_id: bin_id,
      new_schedule_time: scheduled_time,
      color: colorArr,
      master_device_id: group.master_device_id,
    });
  });

  fs.unlinkSync(file.path); // Remove the uploaded file

  if (errors.length > 0) {
    // If there were errors, respond with them
    return res.status(400).json({ errors });
  }

  console.log("Finished");

  // Call the function to update schedules with a delay
  updateSchedulesWithDelay(scheduleDataArray);

  saveDataToFile(cache); // Save updated cache to file
  res.json({ message: "File imported and data updated successfully" });
});

// Get bin details
app.get("/bin", (req, res) => {
  const { group_id, rack_id, bin_id } = req.query;
  updateCache(); // Ensure cache is up-to-date

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

async function scheduleChecker() {
  while (true) {
    updateCache(); // Ensure cache is up-to-date
    var currentTime = new Date();
    var currentHour = currentTime.getHours();
    var currentMinute = currentTime.getMinutes();
    currentHour = "" + currentHour;
    currentMinute = "" + currentMinute;

    currentHour = currentHour.length == 1 ? "0" + currentHour : currentHour;
    currentMinute =
      currentMinute.length == 1 ? "0" + currentMinute : currentMinute;

    cache.forEach((group) => {
      group.racks.forEach((rack) => {
        rack.bins.forEach((bin) => {
          bin.schedules.forEach((schedule) => {
            const [hour, minute] = schedule.time.split(":");
            console.log(
              hour + ":" + minute + "--" + currentHour + ":" + currentMinute
            );

            if (
              schedule.enabled &&
              hour === currentHour &&
              minute === currentMinute
            ) {
              // Perform actions when the schedule matches the current time
              // console.log(`Updating bin ${bin.bin_id} for group ${group.Group_id}`);
              bin.color = schedule.color; // Example action: Update bin color
              bin.clicked = false;
              // Add more logic to handle the bin's action

              //updateScheduleESP(group.Group_id, rack.rack_id, bin.bin_id, schedule.time, schedule.color);
            }
          });
        });
      });
    });

    saveDataToFile(cache);
    // Wait for the next minute before checking again
    await new Promise((resolve) => setTimeout(resolve, 60000));
  }
}

// Update bin schedule
app.put("/bin/update/schedule", (req, res) => {
  const { group_id, rack_id, bin_id, scheduled_index, current_enabled_status } =
    req.body;

  console.log(
    group_id,
    rack_id,
    bin_id,
    scheduled_index,
    current_enabled_status
  );

  updateCache(); // Ensure cache is up-to-date
  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  bin.schedules[scheduled_index].enabled = !current_enabled_status;

  let fail = updateScheduleESP(
    group_id,
    rack_id,
    bin_id,
    scheduled_index,
    current_enabled_status,
    group.master_device_id
  );

  if (fail) {
    res.status(404);
    return;
  }
  saveDataToFile(cache);

  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

// Update bin color

app.post("/bin/update/enabled", (req, res) => {
  const { group_id, rack_id, bin_id } = req.body;
  updateCache(); // Ensure cache is up-to-date

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  const curr = bin.enabled;

  bin.schedules.forEach((element, index) => {
    element.enabled = !curr;

    let fail = updateScheduleESP(
      group_id,
      rack_id,
      bin_id,
      index,
      curr,
      group.master_device_id
    );
    if (fail) {
      res.status(404);
      return;
    }
  });

  bin.enabled = !curr;

  saveDataToFile(cache);

  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

// Toggle clicked
app.post("/bin/update/clicked", (req, res) => {
  const { group_id, rack_id, bin_id } = req.body;
  updateCache(); // Ensure cache is up-to-date
  console.log(group_id, rack_id);

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  bin.clicked = true;

  console.log(group_id, rack_id, bin_id, group.master_device_id);

  let fail = updateBinClicked(
    group_id,
    rack_id,
    bin_id,
    group.master_device_id
  );

  if (fail) {
    res.status(404);
    return;
  }
  console.log("ADDED");
  saveDataToFile(cache);

  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

app.put("/bin/update/color", (req, res) => {
  const { group_id, rack_id, bin_id, new_color } = req.body;
  updateCache(); // Ensure cache is up-to-date

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  bin.color = new_color;
  let fail = updateBinColorESP(
    group_id,
    rack_id,
    bin_id,
    new_color,
    group.master_device_id
  );

  if (fail) {
    res.status(404);
    return;
  }

  saveDataToFile(cache);
  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

app.post("/new/group", (req, res) => {
  const { newGroupid, newGroupDeviceId } = req.body;

  console.log(newGroupid, newGroupDeviceId);
  updateCache(); // Ensure cache is up-to-date

  // Check if a group with the same Group ID already exists
  const existingGroupById = cache.find(
    (group) => group.Group_id === newGroupid
  );

  // Check if a group with the same Device ID already exists
  const existingGroupByDeviceId = cache.find(
    (group) => group.master_device_id === newGroupDeviceId
  );

  if (existingGroupById) {
    return res.status(400).json({ error: "Group with this ID already exists" });
  }

  if (existingGroupByDeviceId) {
    return res
      .status(400)
      .json({ error: "Group with this Device ID already exists" });
  }

  // Create a new group if it doesn't exist
  const newGroup = {
    Group_id: newGroupid,
    master_device_id: newGroupDeviceId,
    racks: [], // Initialize with an empty array for racks
  };

  // Add the new group to the cache
  cache.push(newGroup);

  // let fail = updateADDGroupESP(newGroupid, newGroupDeviceId);

  // if (fail) {
  //   res.status(404).json({ error: "Failed to update the group in ESP" });
  //   return;
  // }

  // Save to static.json
  updateStaticJson(newGroupid, newGroupDeviceId);
  updateLedMacDataExcel(newGroupDeviceId, "add");

  saveDataToFile(cache);
  res.json({ message: "Group added successfully", group: newGroup });
});

app.post("/delete/group", (req, res) => {
  const { groupId } = req.body;

  updateCache(); // Ensure cache is up-to-date

  // Find the index of the group by Group ID
  const groupIndex = cache.findIndex((group) => group.Group_id === groupId);

  if (groupIndex !== -1) {
    // Remove the group from the cache
    const deviceId = cache[groupIndex].master_device_id;
    let removedGroup = cache.splice(groupIndex, 1);
    console.log(deviceId);

    let fail = updateDeleteGroupESP(groupId, deviceId);

    if (fail) {
      res.status(404).json({ error: "Failed to update the group in ESP" });
      return;
    }
    updateStaticJsonDelete(groupId, deviceId);
    // console.log(removedGroup);
    updateLedMacDataExcel(deviceId, "delete");
    if (removedGroup[0].racks[0]) {
      removedGroup[0].racks.forEach((data, index) => {
        updateLedMacDataExcelFinal(data.device_id, "delete");
      });
    }

    // Save to static.json
    saveDataToFile(cache);

    res.json({ message: "Group deleted successfully" });
  } else {
    res.status(404).json({ error: "Group not found" });
  }
});

// Function to update static.json
function updateStaticJsonDelete(groupId, deviceId) {
  const staticFilePath = path.join(__dirname, "static.json");

  console.log(groupId, deviceId);

  let staticData = [];

  // Read existing data
  if (fs.existsSync(staticFilePath)) {
    staticData = JSON.parse(fs.readFileSync(staticFilePath, "utf8"));
  }

  // // Check if the device is already in the static.json
  const existingDeviceIndex = staticData.findIndex(
    (device) => device.master_id === groupId
  );

  if (existingDeviceIndex !== -1) {
    staticData.splice(existingDeviceIndex, 1);
  }

  // // Write back to static.json
  fs.writeFileSync(staticFilePath, JSON.stringify(staticData, null, 2), "utf8");
}

// Function to update static.json
function updateStaticJson(groupId, deviceId) {
  const staticFilePath = path.join(__dirname, "static.json");

  let staticData = [];

  // Read existing data
  if (fs.existsSync(staticFilePath)) {
    staticData = JSON.parse(fs.readFileSync(staticFilePath, "utf8"));
  }

  // Check if the device is already in the static.json
  const existingDeviceIndex = staticData.findIndex(
    (device) => device.ID === deviceId
  );

  const newEntry = {
    IP: "",
    ID: deviceId,
    master_id: groupId,
  };

  if (existingDeviceIndex !== -1) {
    // If it exists, update the entry
    staticData[existingDeviceIndex] = newEntry;
  } else {
    // If it doesn't exist, add the new entry
    staticData.push(newEntry);
  }

  // Write back to static.json
  fs.writeFileSync(staticFilePath, JSON.stringify(staticData, null, 2), "utf8");
}

// Function to update led_mac_data.xlsx
function updateLedMacDataExcel(deviceId, operation) {
  const ledMacDataFilePath = path.join(__dirname, "led_mac_data.xlsx");
  // Load the Excel file
  const workbook = xlsx.readFile(ledMacDataFilePath);
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];

  const excel = xlsx.utils.sheet_to_json(worksheet, { header: 1 });

  // Iterate through the rows to find the device
  for (let i = 1; i < excel.length; i++) {
    if (excel[i][0] === deviceId) {
      excel[i][5] = operation === "add" ? true : false;
      break;
    }
  }

  // Convert JSON data back to sheet format
  const newWorksheet = xlsx.utils.aoa_to_sheet(excel);
  workbook.Sheets[sheetName] = newWorksheet;

  // Write back to the Excel file
  xlsx.writeFile(workbook, ledMacDataFilePath);
}

function updateLedMacDataExcelFinal(deviceId, operation) {
  console.log(deviceId, operation);

  const ledMacDataFilePath = path.join(__dirname, "led_mac_data.xlsx");
  // Load the Excel file
  const workbook = xlsx.readFile(ledMacDataFilePath);
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];

  const excel = xlsx.utils.sheet_to_json(worksheet, { header: 1 });

  // Iterate through the rows to find the device
  for (let i = 1; i < excel.length; i++) {
    if (excel[i][0] === deviceId) {
      if (operation === "add") excel[i][6] = false;
      else excel[i][6] = true;
      // excel[i][5] = true; // Set isMaster to true
      // Set availability to false
      break;
    }
  }

  // Convert JSON data back to sheet format
  const newWorksheet = xlsx.utils.aoa_to_sheet(excel);
  workbook.Sheets[sheetName] = newWorksheet;

  // Write back to the Excel file
  xlsx.writeFile(workbook, ledMacDataFilePath);
}

function readDeviceConfig(id) {
  let workbook;
  try {
    workbook = xlsx.readFile("led_mac_data.xlsx");
  } catch (err) {
    console.log(err);
    throw new Error("Failed to read Excel file");
  }

  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  const users = xlsx.utils.sheet_to_json(sheet);
  // console.log(users);

  const device = users.find((row) => row.ID === id);

  if (!device) {
    throw new Error("Device ID not found");
  }

  return device.mac_arr.split(",").map(Number);
}

app.post("/new/rack", (req, res) => {
  const { Groupid, newWrackid, id } = req.body;
  updateCache(); // Ensure cache is up-to-date
  console.log(Groupid, newWrackid, "--" + id + "--");

  let mac;
  try {
    mac = readDeviceConfig(id);
  } catch (error) {
    return res.status(404).json({ error: error.message });
  }

  const group = cache.find((group) => group.Group_id === Groupid);
  if (!group) return res.status(404).json({ error: "Group not found" });

  // Check if rack already exists in the current group
  const existingRack = group.racks.find((rack) => rack.rack_id === newWrackid);

  if (existingRack) {
    return res.status(400).json({ error: "Rack already exists" });
  }

  const newRack = {
    rack_id: newWrackid,
  };

  function checkArraysEqual(arr1, arr2) {
    if (arr1.length !== arr2.length) return false;
    for (let i = 0; i < arr1.length; i++) {
      if (arr1[i] !== arr2[i]) {
        return false;
      }
    }
    return true;
  }

  const curr_mac = mac;

  let master_mac = null;
  for (const otherGroup of cache) {
    if (otherGroup.Group_id !== Groupid && otherGroup.racks.length > 0) {
      const otherRackMac = otherGroup.racks[0].mac;
      if (checkArraysEqual(otherRackMac, curr_mac)) {
        return res
          .status(400)
          .json({ error: "Master MAC already exists in another group" });
      }
    }
  }

  // If no conflicts found, set master_mac for current group if it exists
  if (group.racks.length > 0) {
    master_mac = group.racks[0].mac;
  }

  if (master_mac && !checkArraysEqual(master_mac, curr_mac)) {
    newRack.master = master_mac;
    newRack.mac = curr_mac;
  } else {
    newRack.mac = curr_mac;
  }

  newRack.device_id = id;

  const ledPins = [12, 25, 26, 27]; // Replace with your actual led pin values
  const buttonPins = [13, 14, 15, 16]; // Replace with your actual button pin values

  const binCount = 4;
  const binsToAdd = Array.from({ length: binCount }, (_, index) => ({
    color: [255, 255, 255],
    led_pin: ledPins[index],
    bin_id: `${newWrackid}_0${index + 1}`,
    button_pin: buttonPins[index],
    schedules: [],
    enabled: true,
    clicked: false,
  }));

  newRack.bins = binsToAdd;

  if (master_mac && checkArraysEqual(master_mac, curr_mac)) {
    group.racks = []; // Clear all racks if MACs match
  }

  // If the rack doesn't exist, add it
  group.racks.push(newRack);

  let fail = updateADDRackESP(
    Groupid,
    newWrackid,
    curr_mac,
    group.master_device_id
  );

  if (fail) {
    res.status(404);
    return;
  }

  updateLedMacDataExcelFinal(id, "add");
  saveDataToFile(cache);
  res.json({ message: "Rack added successfully", rack: newRack });
});

app.post("/delete/rack", (req, res) => {
  const { Groupid, rackId } = req.body;
  console.log(Groupid, rackId);

  updateCache(); // Ensure cache is up-to-date

  const group = cache.find((group) => group.Group_id === Groupid);
  if (!group) {
    return res.status(404).json({ error: "Group not found" });
  }

  const rackIndex = group.racks.findIndex((rack) => rack.rack_id === rackId);
  if (rackIndex === -1) {
    return res.status(404).json({ error: "Rack not found" });
  }

  // Remove the rack from the group
  var removedRack = group.racks.splice(rackIndex, 1);

  console.log(removedRack);

  updateLedMacDataExcelFinal(removedRack[0].device_id, "delete");

  let fail = updateRemoveRackESP(Groupid, rackId, group.master_device_id);

  if (fail) {
    res.status(404);
    return;
  }

  saveDataToFile(cache);

  res.json({ message: "Rack deleted successfully", rackId: rackId });
});

app.post("/new/schedule", (req, res) => {
  const { group_id, wrack_id, bin_id, new_schduled } = req.body;
  updateCache(); // Ensure cache is up-to-date

  console.log(group_id, wrack_id, bin_id, new_schduled);

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === wrack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  // Find the correct position to insert the new schedule based on time
  let inserted = false;
  for (let i = 0; i < bin.schedules.length; i++) {
    const existingTime = bin.schedules[i].time.split(":").map(Number);
    const newTime = new_schduled.time.split(":").map(Number);

    console.log(existingTime, " - -  - ", newTime);

    if (
      newTime[0] < existingTime[0] ||
      (newTime[0] === existingTime[0] && newTime[1] < existingTime[1])
    ) {
      bin.schedules.splice(i, 0, new_schduled); // Insert at the correct position
      inserted = true;
      break;
    }
  }

  // If not inserted, push to the end (means it is the latest time)
  if (!inserted) {
    bin.schedules.push(new_schduled);
  }

  console.log();

  console.log(
    group_id,
    wrack_id,
    bin_id,
    new_schduled.time,
    new_schduled.color
  );
  let fail = updatePushScheduleESP(
    group_id,
    wrack_id,
    bin_id,
    new_schduled.time,
    new_schduled.color,
    group.master_device_id
  );

  if (fail) {
    res.status(404);
    return;
  }
  saveDataToFile(cache);
  res.json({ message: "Schedule added successfully", bin: bin });
});

app.post("/delete/schedule", (req, res) => {
  const { group_id, wrack_id, bin_id, scheduleIndex } = req.body;
  updateCache(); // Ensure cache is up-to-date
  console.log(group_id, wrack_id, bin_id, scheduleIndex);

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === wrack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  if (scheduleIndex < 0 || scheduleIndex >= bin.schedules.length) {
    return res.status(400).json({ error: "Invalid schedule index" });
  }

  const [deletedSchedule] = bin.schedules.splice(scheduleIndex, 1);

  console.log("Deleted Schedule:", deletedSchedule.time);

  const fail = updatePOPScheduleESP(
    group_id,
    wrack_id,
    bin_id,
    deletedSchedule.time,
    group.master_device_id
  );

  if (fail) {
    res.status(500).json({ error: "Failed to update ESP device" });
    return;
  }

  saveDataToFile(cache);
  res.json({ message: "Schedule deleted successfully", bin: bin });
});

let queue = [];
let isAvail = false;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Endpoint to send current server time
app.get("/get-time", async (req, res) => {
  try {
    // Fetch time from the World Time API
    const response = await axios.get(
      "http://worldtimeapi.org/api/timezone/Asia/Kolkata"
    );
    const currentTime = response.data.datetime; // Get the datetime from the response

    // Send the time in ISO format
    res.json({
      time: currentTime,
    });
  } catch (error) {
    console.error("Error fetching time:", error);
    res.status(500).json({ error: "Failed to fetch time" });
  }
});
// Endpoint to send current server time
// app.get("/get-time1", async (req, res) => {
//   try {
//     // // Fetch time from the World Time API
//     // const response = await axios.get(
//     //   "http://worldtimeapi.org/api/timezone/Asia/Kolkata"
//     // );
//     // const currentTime = response.data.datetime; // Get the datetime from the response

//     var currentTime = new Date();
//     // var currentHour = currentTime.getHours();
//     // var currentMinute = currentTime.getMinutes();
//     // Send the time in ISO format
//     res.json({
//       time: currentTime,
//     });
//   } catch (error) {
//     console.error("Error fetching time:", error);
//     res.status(500).json({ error: "Failed to fetch time" });
//   }
// });

console.log("Start-new");

const moment = require("moment-timezone");

app.get("/get-time1", async (req, res) => {
  try {
    // Get the current time in Asia/Kolkata timezone and format it as ISO 8601
    var currentTime = moment.tz("Asia/Kolkata").format(); // This keeps the local timezone offset

    res.json({
      time: currentTime, // Send the time in ISO format for Asia/Kolkata
    });
  } catch (error) {
    console.error("Error fetching time:", error);
    res.status(500).json({ error: "Failed to fetch time" });
  }
});

app.get("/avail", (req, res) => {
  console.log("-----------------------------", queue);
  isAvail = true;
  // Promise();

  sleep(5000);
  // processQueue();

  res.send("Processing queue.");
});

app.get("/stop", (req, res) => {
  isAvail = false;
  res.send("Stopped processing queue.");
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});

//=+-----------------COMMUNICATING WITH ESP------------------------------//

function normalize(data) {
  let normalize_data = (data / 255) * 64;

  return Math.floor(normalize_data);
}

const queues = {}; // Object to maintain separate queues for each server
const unavailableServers = {}; // Object to track temporarily unavailable servers
const processingServers = {}; // Object to track servers currently being processed

const addToQueue = (request) => {
  const { ip } = request;

  // Initialize the queue for the server if it doesn't exist
  if (!queues[ip]) {
    queues[ip] = [];
  }

  // Check if the request is already in the queue to prevent duplicates
  if (
    !queues[ip].some((req) => JSON.stringify(req) === JSON.stringify(request))
  ) {
    queues[ip].push(request);
    console.log(`Queue for ${ip}:`, queues[ip]);
  } else {
    console.log(`Request for ${ip} is already in the queue, skipping.`);
  }
};

const processQueueForServer = async (ip) => {
  // Check if a queue exists and it's not empty
  if (queues[ip] && queues[ip].length > 0 && !processingServers[ip]) {
    processingServers[ip] = true; // Mark the server as being processed

    const requests = queues[ip]; // Get the full queue for the server

    try {
      const response = await axios.post(
        `http://${ip}:8000/`, // Send the entire array to the server
        { requests } // Send the requests array as data
      );
      console.log(
        `All requests processed successfully for ${ip}:`,
        response.data
      );

      // Clear the queue after successful processing
      queues[ip] = [];

      // Pause before the next check (if needed)
      await new Promise((resolve) => setTimeout(resolve, 1000));
    } catch (error) {
      if (error.code === "ECONNREFUSED") {
        console.error(`Connection refused for ${ip}, marking as unavailable.`);
        unavailableServers[ip] = Date.now(); // Mark the server as unavailable
      } else if (error.code === "ECONNRESET") {
        console.error(`Connection reset for ${ip}, stopping the queue.`);
      } else {
        console.error(
          `Error processing requests for ${ip}:`,
          error.response ? error.response.data : error.message
        );
      }
    } finally {
      processingServers[ip] = false; // Mark the server as not being processed anymore
    }
  }
};

// Function to check if any server is available and process its queue
const checkServersAndProcess = async () => {
  const servers = Object.keys(queues);

  for (const ip of servers) {
    // Check if the server is marked unavailable and skip it if so
    if (unavailableServers[ip]) {
      const timeSinceUnavailable = Date.now() - unavailableServers[ip];
      // Retry the server after 10 seconds of being unavailable
      if (timeSinceUnavailable < 10000) {
        console.log(`Server ${ip} is still unavailable, skipping processing.`);
        continue;
      } else {
        console.log(`Rechecking availability of server ${ip}`);
        delete unavailableServers[ip]; // Allow the server to be checked again
      }
    }

    // Check if the queue for the server is not empty
    if (queues[ip] && queues[ip].length > 0) {
      console.log(`Processing queue for server ${ip}`);
      await processQueueForServer(ip);
    }
  }
};

// Periodic listener to check for available servers and process their queues
setInterval(() => {
  console.log("Checking for available servers...");
  checkServersAndProcess();
}, 5000); // Check every 5 seconds

const updateBinClicked = async (group_id, rack_id, bin_id, device_id) => {
  console.log(group_id, rack_id, bin_id, device_id);

  var ip = readStaticIP(device_id);

  console.log(ip);

  if (ip == "") return true;

  console.log("YESSS");

  const request = {
    ip: ip,
    data: {
      group_id,
      rack_id,
      bin_id,
      operation: "click-change",
    },
  };
  addToQueue(request);
  return false;
};

const updateBinColorESP = async (
  group_id,
  rack_id,
  bin_id,
  color,
  device_id
) => {
  var ip = readStaticIP(device_id);

  if (ip == "") return true;
  const normalizedColor = [
    normalize(color[0]),
    normalize(color[1]),
    normalize(color[2]),
  ];
  const request = {
    ip: ip,
    data: {
      group_id,
      rack_id,
      bin_id,
      operation: "color-change",
      color: normalizedColor,
    },
  };
  addToQueue(request);

  return false;
};

const updatePushScheduleESP = (
  group_id,
  rack_id,
  bin_id,
  new_schedule_time,
  color,
  master_device_id
) => {
  console.log(
    "called : " + group_id,
    rack_id,
    bin_id,
    new_schedule_time,
    color,
    master_device_id
  );

  var ip = readStaticIP(master_device_id);

  if (ip == "") return true;
  const normalizedColor = [
    normalize(color[0]),
    normalize(color[1]),
    normalize(color[2]),
  ];

  console.log("saa");

  const request = {
    ip: ip,
    data: {
      group_id,
      rack_id,
      bin_id,
      new_schedule_time,
      operation: "push",
      color: normalizedColor,
    },
  };
  addToQueue(request);

  return false;
};

const updateADDRackESP = (group_id, new_rack_id, mac, device_id) => {
  var ip = readStaticIP(device_id);

  if (ip == "") return true;
  const request = {
    ip: ip,
    data: {
      group_id,
      new_rack_id,
      mac,
      operation: "add-rack",
    },
  };
  addToQueue(request);

  return false;
};
const updatePOPScheduleESP = (
  group_id,
  rack_id,
  bin_id,
  scheduled_time,
  device_id
) => {
  var ip = readStaticIP(device_id);

  if (ip == "") return true;
  const request = {
    ip: ip,
    data: {
      group_id,
      rack_id,
      bin_id,
      scheduled_time,
      operation: "remove-schedule",
    },
  };
  addToQueue(request);

  return false;
};

const updateRemoveRackESP = (group_id, rack_id, device_id) => {
  console.log("updateRemoveRack");
  console.log(group_id, rack_id, device_id);

  var ip = readStaticIP(device_id);
  console.log(ip);

  if (ip == "") return true;
  const request = {
    ip: ip,
    data: {
      group_id,
      rack_id,
      device_id,
      operation: "remove-rack",
    },
  };
  addToQueue(request);

  return false;
};

const updateScheduleESP = (
  group_id,
  rack_id,
  bin_id,
  scheduled_index,
  current_enabled_status,
  device_id
) => {
  var ip = readStaticIP(device_id);
  if (ip == "") return true;
  const request = {
    ip: ip,
    data: {
      group_id,
      rack_id,
      bin_id,
      scheduled_index,
      current_enabled_status,
      operation: "schedule-change",
    },
  };

  addToQueue(request);

  return false;
};

const updateADDGroupESP = (new_group_id, device_id) => {
  var ip = readStaticIP(device_id);

  if (ip == "") return true;
  const request = {
    ip: ip,
    data: {
      new_group_id,
      operation: "add-master",
    },
  };
  addToQueue(request);

  return false;
};

const updateImport = (array, de) => {
  var ip = readStaticIP(device_id);
  console.log(group_id, device_id, ip);

  if (ip == "") return true;
  const request = {
    ip: ip,
    data: {
      group_id,
      operation: "import",
    },
  };
  addToQueue(request);

  return false;
};
const updateDeleteGroupESP = (group_id, device_id) => {
  var ip = readStaticIP(device_id);
  console.log(group_id, device_id, ip);

  if (ip == "") return true;
  const request = {
    ip: ip,
    data: {
      group_id,
      operation: "remove-master",
    },
  };
  addToQueue(request);

  return false;
};

scheduleChecker();
