const express = require("express");
const cors = require("cors");
const fs = require("fs");
const xlsx = require("xlsx");
const multer = require("multer");
const axios = require("axios");
const { error } = require("console");

const app = express();
const port = 5000;

// console.log(serv);
// const { updateBinClicked, updateBinColorESP, updatePushScheduleESP } = serv;

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

const readStaticIP = (id) => {
  try {
    const fileContent = fs.readFileSync("./static.json", "utf8");
    const data = JSON.parse(fileContent);
    console.log(data, id);
    const new_data = data.find((item) => item.ID === id);
    console.log(new_data);
    console.log(new_data.IP, new_data["IP"]);
    return new_data.IP;
  } catch (error) {
    console.error("Error reading static.json:", error);
    throw new Error("Error reading static.json");
  }
};

// // Utility function to write static IP to static.json
// const writeStaticIP = (newIP) => {
//   try {
//     var data = { IP: newIP };
//     fs.writeFileSync("./static.json", JSON.stringify(data, null, 2), "utf8");
//     ip = newIP;
//   } catch (error) {
//     console.error("Error writing static.json:", error);
//     throw new Error("Error writing static.json");
//   }
// };

// app.get("/address/getIP", (req, res) => {
//   try {
//     var staticIP = readStaticIP();
//     res.json({ ip: staticIP });
//   } catch (error) {
//     res.status(500).send("Error reading static IP");
//   }
// });

// // API to update the static IP
// app.post("/address/setIP", (req, res) => {
//   console.log("called");
//   var { ip } = req.body;
//   try {
//     writeStaticIP(ip);
//     res.json({ message: "Static IP updated successfully" });
//   } catch (error) {
//     res.status(500).send("Error updating static IP");
//   }
// });

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
  const id = group.master_id;
  const rack = group.racks.find((rack) => rack.rack_id === bin_details.rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins[bin_details.bin_idx];
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  console.log(bin.clicked);
  bin.clicked = !bin.clicked;
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
    setTimeout(() => {
      updatePushScheduleESP(
        scheduleData.id,
        scheduleData.group_id,
        scheduleData.rack_id,
        scheduleData.bin_id,
        scheduleData.new_schedule_time,
        scheduleData.color
      );
    }, index * 1000); // 1 second delay between each call
  });
};

// Import route
app.post("/import", upload.single("file"), (req, res) => {
  const file = req.file;
  const workbook = xlsx.readFile(file.path);
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];
  const jsonData = xlsx.utils.sheet_to_json(worksheet);

  updateCache(); // Ensure cache is up-to-date

  const scheduleDataArray = [];

  jsonData.forEach((row) => {
    const { Group_id, rack_id, bin_id, scheduled_time, color } = row;
    const group = cache.find((group) => group.Group_id === Group_id);
    if (!group) {
      return res.status(404).json({ error: "Group not found" });
    }
    const id = group.master_id;
    const rack = group.racks.find((rack) => rack.rack_id === rack_id);
    if (!rack) {
      return res.status(404).json({ error: "Rack not found" });
    }
    const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
    if (!bin) {
      return res.status(404).json({ error: "Bin not found" });
    }

    const colorArr = color.split(",").map(Number);
    bin.schedules.push({
      enabled: false,
      time: scheduled_time,
      color: colorArr,
    });

    // Add schedule data to array for delayed processing
    scheduleDataArray.push({
      id: id,
      group_id: Group_id,
      rack_id: rack_id,
      bin_id: bin_id,
      new_schedule_time: scheduled_time,
      color: colorArr,
    });
  });

  saveDataToFile(cache);
  fs.unlinkSync(file.path);

  updateSchedulesWithDelay(scheduleDataArray);

  res.json({ message: "File imported and data updated successfully" });
});

// Get bin details
app.get("/bin", (req, res) => {
  const { group_id, rack_id, bin_id } = req.query;
  updateCache(); // Ensure cache is up-to-date

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });
  const id = group.master_id;
  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

// Update bin schedule
app.put("/bin/update/schedule", (req, res) => {
  const { group_id, rack_id, bin_id, scheduled_index, current_enabled_status } =
    req.body;

  updateCache(); // Ensure cache is up-to-date
  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });
  const id = group.master_id;
  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  bin.schedules[scheduled_index].enabled = !current_enabled_status;

  saveDataToFile(cache);
  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

// Update bin color

// Toggle enabled
app.post("/bin/update/enabled", (req, res) => {
  const { group_id, rack_id, bin_id } = req.body;
  updateCache(); // Ensure cache is up-to-date

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });
  const id = group.master_id;
  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  bin.enabled = !bin.enabled;
  saveDataToFile(cache);

  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

// Update bin color

// Toggle clicked
app.post("/bin/update/clicked", (req, res) => {
  const { group_id, rack_id, bin_id } = req.body;
  updateCache(); // Ensure cache is up-to-date

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });
  const id = group.master_id;
  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  bin.clicked = !bin.clicked;
  updateBinClicked(id, group_id, rack_id, bin_id);
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

  const id = group.master_id;
  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  bin.color = new_color;
  saveDataToFile(cache);
  updateBinColorESP(id, group_id, rack_id, bin_id, new_color);

  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

app.post("/new/group", (req, res) => {
  const { newGroupid } = req.body;
  var id = "KT-1";
  updateCache(); // Ensure cache is up-to-date

  const existingGroup = cache.find((group) => group.Group_id === newGroupid);
  if (existingGroup)
    return res.status(400).json({ error: "Group already exists" });

  const newGroup = {
    Group_id: newGroupid,
    master_id: id,
    racks: [],
  };

  cache.push(newGroup);
  updateADDGroupESP(id, newGroupid);
  saveDataToFile(cache);
  res.json({ message: "Group added successfully", group: newGroup });
});

function readDeviceConfig(id) {
  let workbook;
  try {
    workbook = xlsx.readFile("Device_Config.xlsx");
  } catch (err) {
    console.log(err);
    throw new Error("Failed to read Excel file");
  }

  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  const users = xlsx.utils.sheet_to_json(sheet);
  console.log(users);

  const device = users.find((row) => row.ID === id);
  if (!device) {
    throw new Error("Device ID not found");
  }

  return device.mac_arr.split(",").map(Number);
}

app.post("/new/rack", (req, res) => {
  const { Groupid, newWrackid, id } = req.body;
  updateCache(); // Ensure cache is up-to-date

  let mac;
  try {
    mac = readDeviceConfig(id);
  } catch (error) {
    return res.status(404).json({ error: error.message });
  }

  const group = cache.find((group) => group.Group_id === Groupid);
  if (!group) return res.status(404).json({ error: "Group not found" });
  const master_id = group.master_id;
  // Check if rack already exists in the current group
  const existingRack = group.racks.find((rack) => rack.rack_id === newWrackid);
  if (existingRack)
    return res.status(400).json({ error: "Rack already exists" });

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

  const ledPins = [12, 25, 26, 27]; // Replace with your actual led pin values
  const buttonPins = [13, 14, 15, 16]; // Replace with your actual button pin values

  const binCount = 4;
  const binsToAdd = Array.from({ length: binCount }, (_, index) => ({
    color: [1, 1, 1],
    led_pin: ledPins[index],
    bin_id: `${newWrackid}_0${index + 1}`,
    button_pin: buttonPins[index],
    schedules: [],
    enabled: false,
    clicked: false,
  }));

  newRack.bins = binsToAdd;

  if (master_mac && checkArraysEqual(master_mac, curr_mac)) {
    group.racks = []; // Clear all racks if MACs match
  }
  group.racks.push(newRack);
  updateADDRackESP(master_id ? master_id : id, Groupid, newWrackid, curr_mac);
  saveDataToFile(cache);

  res.json({ message: "Rack added successfully", rack: newRack });
});

app.post("/new/schedule", (req, res) => {
  const { group_id, wrack_id, bin_id, new_schduled } = req.body;
  updateCache(); // Ensure cache is up-to-date

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });
  const id = group.master_id;
  const rack = group.racks.find((rack) => rack.rack_id === wrack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  bin.schedules.push(new_schduled);

  // // If this is the first schedule, update the bin color
  // if (bin.schedules.length === 1) {
  //   bin.color = new_schduled.color;
  // }

  saveDataToFile(cache);

  console.log(
    group_id,
    wrack_id,
    bin_id,
    new_schduled.time,
    new_schduled.color
  );
  updatePushScheduleESP(
    id,
    group_id,
    wrack_id,
    bin_id,
    new_schduled.time,
    new_schduled.color
  );
  res.json({ message: "Schedule added successfully", bin: bin });
});
const readSchedule = () => {
  const data = fs.readFileSync("schedule.json");
  return JSON.parse(data);
};

// Write schedule data to the JSON file
const writeSchedule = (data) => {
  fs.writeFileSync("schedule.json", JSON.stringify(data, null, 2));
};

async function sentReq(id, request) {
  try {
    const response = await axios.post(
      "http://" + request.ip + ":8000/",
      request.data
    );
    console.log(`Request processed successfully for ${id}:`, response.data);
  } catch (error) {
    console.error(
      "Error processing request:",
      error.response ? error.response.data : error.message
    );
  }
}

app.get("/avail/:id", (req, res) => {
  const id = req.params.id;
  let schedule = readSchedule();
  const index = getScheduleIndex(id, schedule);

  if (index === -1) {
    return res.status(404).send(`ID ${id} not found.`);
  }

  if (!schedule[index].isProcessing && !schedule[index].stopProcessing) {
    processQueue(id);
  }

  schedule[index].isAvail = true;
  schedule[index].stopProcessing = false;
  writeSchedule(schedule);
  res.send(`Processing queue for ${id}.`);
});

app.get("/stop/:id", (req, res) => {
  const id = req.params.id;
  let schedule = readSchedule();
  const index = getScheduleIndex(id, schedule);

  if (index === -1) {
    return res.status(404).send(`ID ${id} not found.`);
  }

  schedule[index].isAvail = false;
  schedule[index].stopProcessing = true;
  writeSchedule(schedule);
  res.send(`Stopped processing queue for ${id}.`);
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});

//=+-----------------------------------------------//

const normalize = (data) => {
  let normalize_data = (data / 255) * 64;
  return Math.floor(normalize_data);
};

const getScheduleIndex = (id, schedule) => {
  return schedule.findIndex((item) => item.id === id);
};

const addToQueue = (id, request) => {
  let schedule = readSchedule();
  const index = getScheduleIndex(id, schedule);

  if (index === -1) {
    console.error(`ID ${id} not found.`);
    return;
  }
  if (schedule[index].isAvail) {
    try {
      sentReq(id, request);
      return;
    } catch (err) {
      console.error(err);
    }
  }
  schedule[index].queue.push(request);
  console.log(`Queue for ${id}:`, schedule[index].queue);
  if (!schedule[index].isProcessing && !schedule[index].stopProcessing) {
    processQueue(id);
  }

  writeSchedule(schedule);
};

async function sentReq(id, request) {
  try {
    const response = await axios.post(
      "http://" + request.ip + ":8000/",
      request.data
    );
    console.log(`Request processed successfully for ${id}:`, response.data);
  } catch (error) {
    if (error.code === "ECONNREFUSED") {
    } else if (error.code === "ECONNRESET") {
      console.error("Connection reset, stopping queue processing.");
    } else {
      console.error(
        "Error processing request:",
        error.response ? error.response.data : error.message
      );
    }
  }
}

const processQueue = async (id) => {
  let schedule = readSchedule();
  const index = getScheduleIndex(id, schedule);

  if (index === -1) {
    console.error(`ID ${id} not found.`);
    return;
  }

  if (schedule[index].isProcessing || schedule[index].stopProcessing) {
    return;
  }

  schedule[index].isProcessing = true;
  writeSchedule(schedule);

  while (
    schedule[index].queue.length !== 0 &&
    !schedule[index].stopProcessing
  ) {
    const request = schedule[index].queue[0];
    try {
      await sentReq(id, request);
      schedule[index].queue.shift(); // Remove the request from the queue on success
    } catch (error) {
      console.error("Error processing request, will retry:", error.message);
    }
    writeSchedule(schedule); // Update the schedule after processing each request
  }

  schedule[index].isProcessing = false;
  writeSchedule(schedule);

  if (schedule[index].queue.length > 0 && !schedule[index].stopProcessing) {
    processQueue(id);
  } else if (schedule[index].stopProcessing) {
    console.log(`Queue processing stopped for ${id}.`);
  }
};

// Example function updates with id parameter
const updateBinClicked = async (id, group_id, rack_id, bin_id) => {
  var ip = readStaticIP(id);
  const request = {
    ip: ip,
    data: {
      group_id,
      rack_id,
      bin_id,
      operation: "click-change",
    },
  };
  addToQueue(id, request);
};

const updateBinColorESP = async (id, group_id, rack_id, bin_id, color) => {
  var ip = readStaticIP(id);
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
  addToQueue(id, request);
};

const updatePushScheduleESP = (
  id,
  group_id,
  rack_id,
  bin_id,
  new_schedule_time,
  color
) => {
  var ip = readStaticIP(id);
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
      new_schedule_time,
      operation: "push",
      color: normalizedColor,
    },
  };
  addToQueue(id, request);
};

const updateADDRackESP = (id, group_id, new_rack_id, mac) => {
  var ip = readStaticIP(id);
  const request = {
    ip: ip,
    data: {
      group_id,
      new_rack_id,
      mac,
      operation: "add-rack",
    },
  };
  addToQueue(id, request);
};

const updateADDGroupESP = (id, new_group_id) => {
  var ip = readStaticIP(id);
  const request = {
    ip: ip,
    data: {
      new_group_id,
      operation: "add-master",
    },
  };
  addToQueue(id, request);
};
