const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");

module.exports = buildModule("BoxModule", (m) => {
  const deployer = m.getAccount(0);
  const box = m.contract("Box", [], {
    from: deployer,
  });
  return { box };
});
