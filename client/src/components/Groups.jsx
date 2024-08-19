import React from "react";
import "./Groups.css";

const Groups = ({ data, handleBinClick }) => {
  return (
    <div className="groups-section">
      <h2 className="groups-header">Groups</h2>
      {data.map((group, index) => (
        <div key={index} className="group-container">
          <h3>{group.Group_id}</h3>
          <div className="group-tables">
            {group.racks.map((rack) => (
              <table className="single-column-table" key={rack.rack_id}>
                <thead>
                  <tr>
                    <th>{rack.rack_id}</th>
                  </tr>
                </thead>
                <tbody>
                  {rack.bins.map((bin, rowIndex) => (
                    <tr key={rowIndex}>
                      <td
                        style={{
                          backgroundColor: bin.clicked
                            ? "gray"
                            : `rgb(${bin.color})`,
                        }}
                        onClick={() => {
                          handleBinClick(
                            group.Group_id,
                            rack.rack_id,
                            bin.bin_id
                          );
                        }}
                      >
                        {bin.bin_id}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default Groups;
