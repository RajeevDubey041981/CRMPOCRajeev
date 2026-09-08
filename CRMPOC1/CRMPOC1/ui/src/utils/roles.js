export function roleKey(role) {
  return (role || "").trim().toLowerCase();
}

export function isIndcoolServiceRole(role) {
  const key = roleKey(role);
  return key === "indcool" || key === "indcool service" || key === "indcool_service" || key === "service";
}

export function isSystemAdminRole(role) {
  const key = roleKey(role);
  return key === "admin" || key === "incool";
}

export function isPartnerAdminRole(role) {
  const key = roleKey(role);
  return key === "admin" || key === "incool" || key === "indcool";
}

export function isOperationsAdminRole(role) {
  return isSystemAdminRole(role) || isIndcoolServiceRole(role);
}

export function isServiceTeamRole(role) {
  return isOperationsAdminRole(role);
}
