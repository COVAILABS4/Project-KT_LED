const express = require("express");
const app = express();
const multer = require("multer");
const fs = require("fs");
const cors = require("cors");
const path = require("path");
const moment = require("moment-timezone");
const xlsx = require("xlsx");
app.use(cors());
app.use(express.json()); // To handle JSON in POST/PUT requests

const port = 5000;
// Method to get data from data.json

const RelayManager = require("./RelayManager");

const waiting_time = 10;

const relayManager = new RelayManager(waiting_time);

const get_data = () => {
  try {
    const jsonData = fs.readFileSync("./data.json", "utf8");
    return JSON.parse(jsonData);
  } catch (err) {
    console.error("Error reading JSON file:", err);
    return null;
  }
};

const processRelayData = () => {
  const data = get_data();

  data.forEach((group) => {
    const group_id = group.Group_id;
    // console.log(`Group ID: ${group_id}`);
    relayManager.createGroup(group_id);

    group.racks.forEach((rack) => {
      const rack_id = rack.rack_id;

      relayManager.createRack(group_id, rack_id);
      // console.log(`${group_id}  - -  Rack ID: ${rack_id}`);
    });
  });
};

processRelayData();

const readUsersFromExcel = () => {
  const workbook = xlsx.readFile("user.xlsx");
  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  const users = xlsx.utils.sheet_to_json(sheet);
  return users;
};

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

app.get("/bin", (req, res) => {
  const { group_id, rack_id, bin_id } = req.query;
  const cache = get_data(); // Ensure cache is up-to-date

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

  var cache = get_data(); // Ensure cache is up-to-date
  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  bin.schedules[scheduled_index].enabled = !current_enabled_status;

  set_data(cache);

  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

const upload = multer({ dest: "uploads/" });

// Import Excel and process data
app.post("/import", upload.single("file"), (req, res) => {
  const file = req.file;
  if (!file) return res.status(400).json({ error: "No file uploaded." });

  try {
    // Read the Excel file
    const workbook = xlsx.readFile(file.path);
    const sheetName = workbook.SheetNames[0];
    const worksheet = xlsx.utils.sheet_to_json(workbook.Sheets[sheetName]);

    // Process each row in the Excel sheet
    const cache = get_data();
    worksheet.forEach((row) => {
      const { group_id, rack_id, bin_id, schedule_time, color } = row;
      // const colorArray = color.split(",").map(Number);

      const group = cache.find((group) => group.Group_id === group_id);
      if (!group) return;

      const rack = group.racks.find((rack) => rack.rack_id === rack_id);
      if (!rack) return;

      const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
      if (!bin) return;

      function normalizeColor(color) {
        return Math.round((color / 255) * 65);
      }

      const newSchedule = {
        time: schedule_time,
        enabled: true,
        color: color.split(",").map(Number),
        colorESP: color.split(",").map(Number).map(normalizeColor),
      };

      // Add the schedule to the bin
      bin.schedules.push(newSchedule);
    });

    // Save updated data back to data.json
    set_data(cache);

    // Clear all files in the uploads directory
    fs.readdir("uploads", (err, files) => {
      if (err) throw err;
      for (const file of files) {
        fs.unlink(path.join("uploads", file), (err) => {
          if (err) throw err;
        });
      }
    });

    res.json({ message: "File processed successfully." });
  } catch (error) {
    console.error("Error processing file:", error);
    res.status(500).json({ error: "Failed to process file." });
  }
});

// Sample Excel download endpoint
app.get("/download-sample", (req, res) => {
  const sampleFilePath = path.join(__dirname, "sample.xlsx");
  res.download(sampleFilePath, "sample.xlsx", (err) => {
    if (err) {
      console.error("Error downloading sample file:", err);
      res.status(500).json({ error: "Failed to download sample file." });
    }
  });
});
// Update bin color

app.post("/bin/update/enabled", (req, res) => {
  const { group_id, rack_id, bin_id } = req.body;
  var cache = get_data(); // Ensure cache is up-to-date

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  const curr = bin.enabled;

  bin.schedules.forEach((element, index) => {
    element.enabled = !curr;
  });

  bin.enabled = !curr;

  set_data(cache);

  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

// Path to click.json
const clickDataFilePath = path.join(__dirname, "./click.json");

// Function to get click data from JSON file
function get_click_data() {
  try {
    if (fs.existsSync(clickDataFilePath)) {
      const data = fs.readFileSync(clickDataFilePath, "utf8");
      return JSON.parse(data);
    } else {
      const defaultData = {};
      fs.writeFileSync(clickDataFilePath, JSON.stringify(defaultData, null, 2));
      return defaultData;
    }
  } catch (error) {
    console.error("Error reading click data:", error);
    return {};
  }
}

// Function to set click data to JSON file
function set_click_data(newData) {
  try {
    fs.writeFileSync(clickDataFilePath, JSON.stringify(newData, null, 2));
    console.log("Click data updated successfully.");
  } catch (error) {
    console.error("Error writing click data:", error);
  }
}

// Updated endpoint to handle bin clicks
app.post("/bin/update/clicked", (req, res) => {
  const { group_id, rack_id, bin_id } = req.body;
  var cache = get_data(); // Ensure cache is up-to-date

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === rack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const binIndex = rack.bins.findIndex((bin) => bin.bin_id === bin_id);
  if (binIndex === -1) return res.status(404).json({ error: "Bin not found" });

  // Print the bin index
  console.log("Bin Index:", binIndex);

  const bin = rack.bins[binIndex];
  bin.clicked = true;
  relayManager.changeState(group_id, rack_id, binIndex, "OFF");

  let kit_id = rack.KIT_ID;

  // Update click.json with the bin_id under the corresponding KIT_ID
  let clickData = get_click_data();
  if (!clickData[kit_id]) {
    clickData[kit_id] = [];
  }

  // Add bin_id if not already present
  // if (!clickData[kit_id].includes(bin_id)) {
  clickData[kit_id].push(binIndex);
  // }

  var bin_queue = get_bin_queue();
  // console.log(bin_queue[bin_idx]);
  console.log(bin_queue);

  if (bin_queue[rack.KIT_ID][binIndex].length !== 0) {
    let next_color = bin_queue[rack.KIT_ID][binIndex].shift();
    bin.color = next_color.color;
    bin.colorESP = next_color.colorESP;
    bin.clicked = false;
    relayManager.changeState(group_id, rack_id, binIndex, "ON");
  } else {
    bin.clicked = true;
    // foundBin.color = next_color;
  }

  // console.log("1113", foundBin);

  set_bin_queue(bin_queue);

  set_click_data(clickData); // Save updated click data

  // console.log(kit_id, bin_id);

  set_data(cache);

  const clone = JSON.parse(JSON.stringify(bin));
  clone.group_id = group_id;
  clone.rack_id = rack_id;
  res.json(clone);
});

// Endpoint to get click data by KIT_ID
app.get("/get-click/:id", (req, res) => {
  const kit_id = req.params.id;

  console.log("KIT ID:", kit_id);

  const clickData = get_click_data();
  console.log("Current Click Data:", clickData);

  if (clickData[kit_id] && clickData[kit_id].length > 0) {
    // Send the response with click data
    res.json(clickData[kit_id]);

    // Clear the array for the specified KIT_ID after a successful response
    clickData[kit_id] = [];

    // Save the updated click data
    set_click_data(clickData);

    console.log(`Click data for KIT_ID ${kit_id} has been cleared.`);
  } else {
    res.status(404).json({ error: "No clicks found for the specified KIT_ID" });
  }
});

// Method to set data in data.json
const set_data = (newData) => {
  try {
    fs.writeFileSync("./data.json", JSON.stringify(newData, null, 2), "utf8");
    console.log("Data successfully updated!");
    return true;
  } catch (err) {
    console.error("Error writing to JSON file:", err);
    return false;
  }
};

// Endpoint to get rack details by KIT_ID
app.get("/get-data/:id", (req, res) => {
  const kitId = req.params.id;
  console.log("Called - - -", kitId);

  // Use get_data() to fetch the latest data
  const data = get_data();
  if (!data) {
    res.status(500).send({ message: "Error reading data" });
    return;
  }

  let foundRack = null;

  // Search for the rack matching the given KIT_ID
  data.forEach((group) => {
    group.racks.forEach((rack) => {
      if (rack.KIT_ID === kitId) {
        foundRack = rack;
      }
    });
  });

  if (foundRack) {
    res.json(foundRack);
  } else {
    res.status(200).send({ message: "Rack not found" });
  }
});

// New endpoint to update the clicked status of a bin
app.post("/click/:id", (req, res) => {
  const kitId = req.params.id;
  const { rack_id, bin_idx } = req.body; // Extracting rack_id and bin_id from the request body

  console.log(
    `Updating click status for KIT_ID: ${kitId}, rack_id: ${rack_id}, bin_idx: ${bin_idx}`
  );

  // Use get_data() to fetch the latest data
  const data = get_data();
  if (!data) {
    return res.status(500).send({ message: "Error reading data" });
  }

  let foundRack = null;
  let foundBin = null;

  let foundGroupId = "";

  var bin_queue = get_bin_queue();

  // Search for the rack and bin matching the provided ids
  data.forEach((group) => {
    group.racks.forEach((rack) => {
      if (rack.KIT_ID === kitId && rack.rack_id === rack_id) {
        foundGroupId = group.Group_id;
        foundRack = rack;
        console.log(foundRack);

        foundBin = rack["bins"][bin_idx];
      }
    });
  });

  //   console.log(foundBin);

  // console.log("1111", foundBin);

  // If the rack and bin are found, update the clicked status
  if (foundRack && foundBin) {
    // console.log("1112", foundBin);
    console.log(bin_queue[foundRack.KIT_ID][bin_idx]);

    if (bin_queue[foundRack.KIT_ID][bin_idx].length !== 0) {
      let next_color = bin_queue[foundRack.KIT_ID][bin_idx].shift();
      foundBin.color = next_color.color;
      foundBin.colorESP = next_color.colorESP;
    } else {
      foundBin.clicked = true;
      relayManager.changeState(foundGroupId, rack_id, bin_idx, "OFF");
      // foundBin.color = next_color;
    }

    // console.log("1113", foundBin);

    set_bin_queue(bin_queue);
    if (set_data(data)) {
      return res.send({ message: "Clicked status updated successfully!" });
    } else {
      return res.status(500).send({ message: "Failed to update data" });
    }
  } else {
    return res.status(404).send({ message: "Rack or Bin not found" });
  }
});

app.post("/new/rack", (req, res) => {
  const { Groupid, newWrackid, kitId } = req.body;
  console.log(Groupid, newWrackid);

  // Get the current cache data
  var cache = get_data();

  // Check if the kitId is already present in any group
  const kitIdExists = cache.some((group) =>
    group.racks.some((rack) => rack.KIT_ID === kitId)
  );

  if (kitIdExists) {
    return res.status(400).json({ error: "Kit ID already exists" });
  }

  // Find the specified group
  const group = cache.find((group) => group.Group_id === Groupid);
  if (!group) return res.status(404).json({ error: "Group not found" });

  // Check if rack already exists in the current group
  const existingRack = group.racks.find((rack) => rack.rack_id === newWrackid);
  if (existingRack) {
    return res.status(400).json({ error: "Rack already exists" });
  }

  var bin_queue = get_bin_queue();

  if (!bin_queue[kitId]) {
    bin_queue[kitId] = {
      0: [],
      1: [],
      2: [],
      3: [],
    }; // Initialize as an empty array if it doesn't exist
  }

  set_bin_queue(bin_queue);
  const isMaster = group.racks.length === 0;

  // Create the new rack
  const newRack = {
    rack_id: newWrackid,
    KIT_ID: kitId,
    master: false,
    buzzer_on: false,
    relay_on: false,
  };
  // Master
  if (isMaster) {
    newRack.master = true;
  }

  const ledPins = [12, 25, 26, 27]; // Replace with your actual led pin values
  const buttonPins = [13, 14, 15, 16]; // Replace with your actual button pin values

  const binCount = 4;
  const binsToAdd = Array.from({ length: binCount }, (_, index) => ({
    color: [255, 255, 255],
    colorESP: [0, 0, 0],
    led_pin: ledPins[index],
    bin_id: `${newWrackid}_0${index + 1}`,
    button_pin: buttonPins[index],
    schedules: [],
    enabled: true,
    clicked: true,
  }));

  newRack.bins = binsToAdd;

  // Add the new rack to the group
  group.racks.push(newRack);

  // Save the updated cache
  set_data(cache);

  // Update click.json to include the KIT_ID key
  let clickData = get_click_data();
  if (!clickData[kitId]) {
    clickData[kitId] = []; // Initialize as an empty array if it doesn't exist
  }

  relayManager.createRack(Groupid, newWrackid);

  // Save the updated click data
  set_click_data(clickData);

  res.json({ message: "Rack added successfully", rack: newRack });
});

app.post("/delete/rack", (req, res) => {
  const { Groupid, rackId } = req.body;
  console.log(Groupid, rackId);

  var cache = get_data();
  const group = cache.find((group) => group.Group_id === Groupid);
  if (!group) {
    return res.status(404).json({ error: "Group not found" });
  }

  const rackIndex = group.racks.findIndex((rack) => rack.rack_id === rackId);
  if (rackIndex === -1) {
    return res.status(404).json({ error: "Rack not found" });
  }

  // Retrieve the KIT_ID of the rack to be deleted
  const kitIdToRemove = group.racks[rackIndex].KIT_ID;

  // Remove the rack from the group
  group.racks.splice(rackIndex, 1);

  // Save the updated cache
  set_data(cache);

  var bin_queue = get_bin_queue();
  console.log(bin_queue);

  console.log(kitIdToRemove);

  if (bin_queue["" + kitIdToRemove]) {
    console.log(bin_queue["" + kitIdToRemove]);

    delete bin_queue["" + kitIdToRemove];
  }

  console.log(bin_queue);

  set_bin_queue(bin_queue);

  // Update click.json by removing the KIT_ID
  let clickData = get_click_data();

  // Check if KIT_ID exists in click.json and delete it
  if (clickData[kitIdToRemove]) {
    delete clickData[kitIdToRemove];
  }

  // Save the updated click data
  set_click_data(clickData);
  relayManager.removeRack(Groupid, rackId);

  res.json({ message: "Rack deleted successfully", rackId: rackId });
});

// Get data route
app.get("/data", (req, res) => {
  try {
    const data = get_data();
    res.json(data);
  } catch (error) {
    res.status(500).send("Error reading data.json");
  }
});

app.post("/new/schedule", (req, res) => {
  const { group_id, wrack_id, bin_id, new_schduled } = req.body;
  var cache = get_data();

  console.log(group_id, wrack_id, bin_id, new_schduled);

  const group = cache.find((group) => group.Group_id === group_id);
  if (!group) return res.status(404).json({ error: "Group not found" });

  const rack = group.racks.find((rack) => rack.rack_id === wrack_id);
  if (!rack) return res.status(404).json({ error: "Rack not found" });

  const bin = rack.bins.find((bin) => bin.bin_id === bin_id);
  if (!bin) return res.status(404).json({ error: "Bin not found" });

  // Check if a schedule with the same time already exists, replace it if found
  let replaced = false;
  for (let i = 0; i < bin.schedules.length; i++) {
    const existingTime = bin.schedules[i].time.split(":").map(Number);
    const newTime = new_schduled.time.split(":").map(Number);

    if (existingTime[0] === newTime[0] && existingTime[1] === newTime[1]) {
      // Replace the existing schedule with the new one
      bin.schedules[i] = new_schduled;
      replaced = true;
      break;
    }
  }

  // If not replaced, find the correct position to insert the new schedule
  if (!replaced) {
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
  }

  set_data(cache);
  res.json({
    message: replaced
      ? "Schedule replaced successfully"
      : "Schedule added successfully",
    bin: bin,
  });
});

app.post("/delete/schedule", (req, res) => {
  const { group_id, wrack_id, bin_id, scheduleIndex } = req.body;

  var cache = get_data();

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

  set_data(cache);
  res.json({ message: "Schedule deleted successfully", bin: bin });
});

// Endpoint to add a new station
app.post("/new/group", (req, res) => {
  const { newGroupId } = req.body;
  console.log(req.body);

  if (!newGroupId) {
    return res.status(400).json({ error: "Station Name is required" });
  }

  const data = get_data();
  if (data.find((group) => group.Group_id === newGroupId)) {
    return res.status(400).json({ error: "Station already exists" });
  }

  data.push({ Group_id: newGroupId, racks: [] });
  set_data(data);

  relayManager.createGroup(newGroupId);

  res.status(201).json({ message: "Station added successfully" });
});

app.post("/delete/group", (req, res) => {
  const { groupId } = req.body;
  var cache = get_data(); // Ensure cache is up-to-date

  var bin_queue = get_bin_queue();

  var click = get_click_data();

  const groupIndex = cache.findIndex((group) => group.Group_id === groupId);
  if (groupIndex === -1) {
    return res.status(404).json({ error: "Group not found" });
  }

  for (let index = 0; index < cache[groupIndex]["racks"].length; index++) {
    console.log(bin_queue[cache[groupIndex]["racks"][index].KIT_ID]);

    delete bin_queue[cache[groupIndex]["racks"][index].KIT_ID];
    delete click[cache[groupIndex]["racks"][index].KIT_ID];
  }

  // Remove the group from the data
  cache.splice(groupIndex, 1);
  set_data(cache);
  set_click_data(click);
  set_bin_queue(bin_queue);

  relayManager.removeGroup(groupId);

  res.json({ message: "Group deleted successfully." });
});

function get_bin_queue() {
  try {
    if (fs.existsSync(binQueueFilePath)) {
      const data = fs.readFileSync(binQueueFilePath, "utf8");
      return JSON.parse(data);
    } else {
      const defaultQueue = { 0: [], 1: [], 2: [], 3: [] };
      fs.writeFileSync(binQueueFilePath, JSON.stringify(defaultQueue));
      return defaultQueue;
    }
  } catch (error) {
    console.error("Error reading bin queue:", error);
    return { 0: [], 1: [], 2: [], 3: [] };
  }
}

const binQueueFilePath = path.join(__dirname, "bin_queue.json");

// Set bin queue to JSON file
function set_bin_queue(binQueue) {
  try {
    fs.writeFileSync(binQueueFilePath, JSON.stringify(binQueue, null, 2));
    console.log("Bin queue updated successfully.");
  } catch (error) {
    console.error("Error writing bin queue:", error);
  }
}
async function scheduleChecker() {
  while (true) {
    const cache = get_data();
    const currentTime = new Date();
    const currentHour = String(currentTime.getHours()).padStart(2, "0");
    const currentMinute = String(currentTime.getMinutes()).padStart(2, "0");

    // Fetch the current bin queue
    let binQueue = get_bin_queue();

    cache.forEach((group) => {
      group.racks.forEach((rack) => {
        rack.bins.forEach((bin, index) => {
          bin.schedules.forEach((schedule) => {
            const [scheduleHour, scheduleMinute] = schedule.time.split(":");

            if (
              schedule.enabled &&
              scheduleHour === currentHour &&
              scheduleMinute === currentMinute
            ) {
              if (bin.clicked) {
                // Example action: Update bin color
                bin.color = schedule.color;
                console.log(
                  `Bin ${bin.bin_id} updated color to`,
                  schedule.color
                );

                bin.colorESP = schedule.colorESP;
                bin.clicked = false; // Reset clicked status
                relayManager.changeState(
                  group.Group_id,
                  rack.rack_id,
                  index,
                  "ON"
                );
              } else {
                // Add color to queue for missed schedule
                if (!binQueue[rack.KIT_ID][index])
                  binQueue[rack.KIT_ID][index] = [];
                binQueue[rack.KIT_ID][index].push({
                  color: schedule.color,
                  colorESP: schedule.colorESP,
                });
                console.log(
                  `Schedule missed for bin ${index}, color added to queue`
                );
              }
            }
          });
        });
      });
    });

    // Update bin queue file
    set_bin_queue(binQueue);
    set_data(cache);

    // Wait for the next minute before checking again
    await new Promise((resolve) => setTimeout(resolve, 60000));
  }
}

// Function to check bins' clicked status and update buzzer status
async function checkBinsAndUpdateBuzzer() {
  while (true) {
    console.log("Checking for Buzzer State");

    let data = get_data();

    for (let i = 0; i < data.length; i++) {
      let group = data[i];
      let anyClickedFalse = false;
      for (let j = 0; j < group.racks.length; j++) {
        let rack = group.racks[j];

        for (let k = 0; k < rack.bins.length; k++) {
          let bin = rack.bins[k];

          if (!bin.clicked) {
            anyClickedFalse = true;

            break;
          }
        }

        if (anyClickedFalse) break;
      }

      if (anyClickedFalse) {
        console.log("Buzzer is On for " + group.Group_id);
        group.racks[0].buzzer_on = true;
      } else if (group.racks[0]) {
        group.racks[0].buzzer_on = false;
      }
    }

    set_data(data);

    // Wait for the next minute before checking again
    await new Promise((resolve) => setTimeout(resolve, 10000));
  }
}

const lengthFilePath = path.join(__dirname, "length.json");

// Function to read the length from the JSON file
const getLengthFromFile = () => {
  try {
    const data = fs.readFileSync(lengthFilePath, "utf8");
    const parsedData = JSON.parse(data);
    return parsedData.length;
  } catch (err) {
    console.error("Error reading the length file:", err);
    return null;
  }
};
const getRackLengthFromFile = () => {
  try {
    const data = fs.readFileSync(lengthFilePath, "utf8");
    const parsedData = JSON.parse(data);
    return parsedData.rack_length;
  } catch (err) {
    console.error("Error reading the length file:", err);
    return null;
  }
};
const getScheduleLengthFromFile = () => {
  try {
    const data = fs.readFileSync(lengthFilePath, "utf8");
    const parsedData = JSON.parse(data);
    return parsedData.schedule_length;
  } catch (err) {
    console.error("Error reading the length file:", err);
    return null;
  }
};

const getAllLengthData = () => {
  try {
    const data = fs.readFileSync(lengthFilePath, "utf8");
    const parsedData = JSON.parse(data);
    return parsedData;
  } catch (err) {
    console.error("Error reading the length file:", err);
    return null;
  }
};

// Function to write the new length to the JSON file
const setLengthToFile = (newLength, type) => {
  let data = getAllLengthData();

  try {
    if (type === "sta") data = { ...data, length: newLength };
    else if (type === "rack") data = { ...data, rack_length: newLength };
    else if (type === "sch") data = { ...data, schedule_length: newLength };

    fs.writeFileSync(lengthFilePath, JSON.stringify(data, null, 2), "utf8");
  } catch (err) {
    console.error("Error writing to the length file:", err);
  }
};

// Endpoint to get the length
app.get("/get-length/:type", (req, res) => {
  const type = req.params.type;
  let length = 0;
  if (type === "sta") length = getLengthFromFile();
  else if (type === "rack") length = getRackLengthFromFile();
  else if (type === "sch") length = getScheduleLengthFromFile();
  if (length !== null) {
    res.json({ length });
  } else {
    res.status(500).json({ error: "Failed to read length from file" });
  }
});

// Endpoint to set the length
app.post("/set-length/:type", (req, res) => {
  const type = req.params.type;

  const { newLength } = req.body;

  // Validate that newLength is a number
  if (typeof newLength !== "number") {
    return res.status(400).json({ error: "Length must be a number" });
  }

  // Set the new length in the JSON file
  setLengthToFile(newLength, type);
  res.json({ message: "Length updated successfully", length: newLength });
});

app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});

scheduleChecker();

checkBinsAndUpdateBuzzer();

async function checkRelayStates() {
  while (true) {
    relayManager.checkGroupState();

    relayManager.printGroupsAndRacks();
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
}

checkRelayStates();
