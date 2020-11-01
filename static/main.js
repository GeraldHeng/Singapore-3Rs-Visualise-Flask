$(document).ready(function () {
  $("#tableBtn").click(function () {
    $("#tableSection").addClass("toggle-on");
    $("#tableSection").removeClass("toggle-off");
    $("#chartSection").addClass("toggle-off");
    $("#chartSection").removeClass("toggle-on");
  });
  $("#chartBtn").click(function () {
    $("#chartSection").addClass("toggle-on");
    $("#chartSection").removeClass("toggle-off");
    $("#tableSection").addClass("toggle-off");
    $("#tableSection").removeClass("toggle-on");
  });

  validateForm();
});

function validateForm() {
  $.validator.addMethod(
    "greaterThan",
    function (value, element, param) {
      return this.optional(element) || parseInt(value) >= parseInt($(param).val());
    },
    "Invalid value"
  );

  $("#searchForm").validate({
    rules: {
      start_year: {
        required: true,
        minlength: 4,
        maxlength: 4,
      },
      end_year: {
        required: true,
        minlength: 4,
        maxlength: 4,
        greaterThan: "#startYear",
      },
    },
    messages: {
      start_year: {
        required: "Please provide a start year",
        minlength: "Start year need to be 4 digits",
      },
      end_year: {
        required: "Please provide a end year",
        minlength: "End year need to be 4 digits",
        greaterThan: "End year need to be greater than the start year",
      }
    },
    submitHandler: function (form) {
      form.submit();
    },
  });
}

function isNumberKey(evt) {
  var charCode = evt.which ? evt.which : evt.keyCode;
  if (charCode != 46 && charCode > 31 && (charCode < 48 || charCode > 57)) return false;
  return true;
}

function sendEmail() {
  var email = document.getElementById("userEmail").value;
  console.log(email);
  $.post("/submit-email", { email: email }, function (data) {
    if (data === "True") {
      if ($("#alert").find("div.alert").length == 0) {
        $("#alert").append(
          "<div class='alert alert-success alert-dismissable' style='z-index:1;'> <button type='button' class='close' data-dismiss='alert'  aria-hidden='true'>&times;</button> Successful! email sent successfully.</div>"
        );
      }
    } else {
      if ($("#alert").find("div.alert").length == 0) {
        $("#alert").append(
          "<div class='alert alert-danger alert-dismissable' style='z-index:1;'> <button type='button' class='close' data-dismiss='alert'  aria-hidden='true'>&times;</button> Unsuccessful! Please try sending the email again!</div>"
        );
      }
    }
  });
}
