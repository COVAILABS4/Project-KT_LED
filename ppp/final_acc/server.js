const express = require("express");
const cors = require("cors");
const fs = require("fs");
const xlsx = require("xlsx");
const multer = require("multer");
const axios = require("axios");

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

// Utility function to write static IP to static.json
const writeStaticIP = (newIP, id) => {
  try {
    // Read the existing data from the file
    let data = [];
    if (fs.existsSync("./static.json")) {
      data = JSON.parse(fs.readFileSync("./static.json", "utf8"));
    }

    // Find the object with the matching ID
    const index = data.findIndex((item) => item.ID === id);

    if (index !== -1) {
      // Update the IP if the ID is found
      data[index].IP = newIP;
    } else {
      // Add a new object if the ID is not found
      data.push({ IP: newIP, ID: id });
    }

    // Write the updated data back to the file
    fs.writeFileSync("./static.json", JSON.stringify(data, null, 2), "utf8");
  } catch (error) {
    console.error("Error writing static.json:", error);
    throw new Error("Error writing static.json");
  }
};

app.get("/address/getIP/:id", (req, res) => {
  try {
    const { id } = req.params;

    console.log(id);
    var staticIP = readStaticIP(id);

    if (staticIP == "") res.status(404);
    console.log(staticIP);
    res.json({ ip: staticIP });
  } catch (error) {
    res.status(500).send("Error reading static IP");
  }
});

// API to update the static IP
app.post("/address/setIP", (req, res) => {
  var { ip, device_id } = req.body;
  try {
    writeStaticIP(ip, device_id);
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

function denormalize(color) {
  var new_color = Math.floor((color / 64) * 255);

  return new_color;
}
app.post("/color/update", (req, res) => {
  console.log("color Called");
  const bin_details = req.body;
  console.log(bin_details);
  const color = bin_details.color;
  updateCache(); // Ensure cache is up-to-date

  let group = cache.find((group) => group.Group_id === bin_details.group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === bin_details.rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins[bin_details.bin_idx];
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  for (let index = 0; index < color.length; index++) {
    color[index] = denormalize(color[index]);
  }
  bin.color = color;
  bin.clicked = false;
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
  console.log("Fined--2 : " + scheduleDataArray);

  scheduleDataArray.forEach((scheduleData, index) => {
    setTimeout(() => {
      console.log(scheduleData);

      let fail = updatePushScheduleESP(
        scheduleData.group_id,
        scheduleData.rack_id,
        scheduleData.bin_id,
        scheduleData.new_schedule_time,
        scheduleData.color,
        scheduleData.master_device_id
      );

      if (fail) return true;
    }, index * 1000); // 1 second delay between each call
  });

  return false;
};

// Import route
app.post("/import", upload.single("file"), (req, res) => {
  console.log("Called");

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
    const rack = group.racks.find((rack) => rack.rack_id === rack_id);
    if (!rack) {
      return res.status(404).json({ error: "Rack not found" });
    }
    const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
    if (!bin) {
      return res.status(404).json({ error: "Bin not found" });
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

  console.log("Fined");

  // Call the function to update schedules with a delay
  // let fail = updateSchedulesWithDelay(scheduleDataArray);

  // if (fail) {
  //   res.status(404);
  //   return;
  // }
  saveDataToFile(cache);
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

  updateCache(); // Ensure cache is up-to-date
  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  bin.schedules[scheduled_index].enabled = !current_enabled_status;

  var fail = updateScheduleESP(
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

    var fail = updateScheduleESP(
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

// Update bin color

// Toggle clicked
app.post("/bin/update/clicked", (req, res) => {
  const { group_id, rack_id, bin_id } = req.body;
  updateCache(); // Ensure cache is up-to-date

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  bin.clicked = true;

  var fail = updateBinClicked(
    group_id,
    rack_id,
    bin_id,
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
  var fail = updateBinColorESP(
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

  // Find the index of the existing group by Group ID (if any)
  const existingGroupIndexById = cache.findIndex(
    (group) => group.Group_id === newGroupid
  );

  // Find the index of the existing group by Device ID (if any)
  const existingGroupIndexByDeviceId = cache.findIndex(
    (group) => group.master_device_id === newGroupDeviceId
  );

  const newGroup = {
    Group_id: newGroupid,
    master_device_id: newGroupDeviceId,
    racks: [], // Initialize with an empty array for racks
  };

  if (existingGroupIndexById !== -1) {
    // If the group exists by Group ID, replace it
    cache[existingGroupIndexById] = newGroup;
  } else if (existingGroupIndexByDeviceId !== -1) {
    // If the group exists by Device ID, replace it
    cache[existingGroupIndexByDeviceId] = newGroup;
  } else {
    // If the group doesn't exist by either ID, add it
    cache.push(newGroup);
  }

  var fail = updateADDGroupESP(newGroupid, newGroupDeviceId);

  if (fail) {
    res.status(404).json({ error: "Failed to update the group in ESP" });
    return;
  }

  saveDataToFile(cache);
  res.json({ message: "Group added or updated successfully", group: newGroup });
});

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

  // Check if rack already exists in the current group
  const existingRackIndex = group.racks.findIndex(
    (rack) => rack.rack_id === newWrackid
  );

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

  if (existingRackIndex !== -1) {
    // If the rack exists, replace it
    group.racks[existingRackIndex] = newRack;
  } else {
    // If the rack doesn't exist, add it
    group.racks.push(newRack);
  }

  var fail = updateADDRackESP(
    Groupid,
    newWrackid,
    curr_mac,
    group.master_device_id
  );

  if (fail) {
    res.status(404);
    return;
  }

  saveDataToFile(cache);

  res.json({ message: "Rack added or updated successfully", rack: newRack });
});

app.post("/new/schedule", (req, res) => {
  const { group_id, wrack_id, bin_id, new_schduled } = req.body;
  updateCache(); // Ensure cache is up-to-date

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
  var fail = updatePushScheduleESP(
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

let queue = [];
let isAvail = false;

app.get("/avail", (req, res) => {
  console.log("-----------------------------", queue);
  isAvail = true;
  processQueue();

  res.send("Processing queue.");
});

app.get("/stop", (req, res) => {
  isAvail = false;
  res.send("Stopped processing queue.");
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});

//=+-----------------------------------------------//

function normalize(data) {
  let normalize_data = (data / 255) * 64;

  return Math.floor(normalize_data);
}

const addToQueue = (request) => {
  queue.push(request);

  console.log(queue);
  if (isAvail) processQueue();
};

const processQueue = async () => {
  let i = 0;

  while (queue.length !== 0 && i < 10) {
    const request = queue[0];
    try {
      const response = await axios.post(
        "http://" + request.ip + ":8000/",
        request.data
      );
      console.log("Request processed successfully:", response.data);
      queue.shift();
      i++;
      if (i == 10) return;
      await new Promise((resolve) => setTimeout(resolve, 1000));
    } catch (error) {
      if (error.code === "ECONNREFUSED") {
        console.error("Connection refused, retrying in 1 second...");
        await new Promise((resolve) => setTimeout(resolve, 1000));
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
};

const updateBinClicked = async (group_id, rack_id, bin_id, device_id) => {
  var ip = readStaticIP(device_id);
  if (ip == "") return true;
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

// Start the schedule checker function
scheduleChecker();
