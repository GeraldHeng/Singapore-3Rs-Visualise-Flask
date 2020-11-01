$(document).ready(function () {
  $("#reviewEventModal").on("show.bs.modal", function (event) {
    var button = $(event.relatedTarget);
    var rowId = button.data("id");
    document.getElementById("rowId").value = rowId;
  });
});

function addEvent() {
  var startYear = document.getElementById("startYear").value;
  var startQuarter = document.getElementById("startQuarter").value;
  var endYear = document.getElementById("endYear").value;
  var endQuarter = document.getElementById("endQuarter").value;
  var event = document.getElementById("event").value;

  $.post("/add-event", { startYear: startYear, startQuarter: startQuarter, endYear: endYear, endQuarter: endQuarter, event: event }, function (data) {
    if (data == "True") {
      location.reload();
    }
  });
}

function reviewStatus(action) {
  var adminPassword = document.getElementById("adminPassword").value;
  var rowId = document.getElementById("rowId").value;
  $.post("/review-status", { adminPassword: adminPassword, action: action, rowId: rowId }, function (data) {
    if (data == "True") {
      location.reload();
    }
  });
}
