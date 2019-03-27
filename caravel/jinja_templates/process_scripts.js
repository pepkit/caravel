$SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
const sleep = (milliseconds) => {
return new Promise(resolve => setTimeout(resolve, milliseconds))
}
// subproject activation
$(function() {
  $('a#activate_subproject').bind('click', function() {
    $.getJSON($SCRIPT_ROOT + '/_background_subproject', {
      sp: $('select[name="subprojects"]').val(),
    }, function(data) {
      $("#subproj_txt").text(data.subproj_txt);
      $("#sample_count").text(data.sample_count);
    });
    document.getElementById("deactivate_btn").disabled = false;
    sleep(100).then(() => {
      render_summary_notice()
    })
  });
});
// subproject deactivation
$(function() {
  $('a#deactivate_subproject').bind('click', function() {
    $.getJSON($SCRIPT_ROOT + '/_background_subproject', {
      sp: "None",
    }, function(data) {
      $("#subproj_txt").text(data.subproj_txt);
      $("#sample_count").text(data.sample_count);
    });
    document.getElementById("deactivate_btn").disabled = true;
    sleep(100).then(() => {
      render_summary_notice()
    })
  });
});

function render_options() {
        $.getJSON($SCRIPT_ROOT + '/_background_options', {
      act: $('select[name="actions"]').val(),
    }, function(data) {
      $("div#options").html(data.options);
    });
    return false;
}
$(function() {
  // The function is triggered on page load and with the "select#show_options" change
  render_options()
  $('select#show_options').bind('change', render_options);
});
function render_summary_notice() {
    $.getJSON($SCRIPT_ROOT + '/_background_summary_notice', {
    }, function(data) {
      if(data.present == "0"){
        document.getElementById("summary_btn").disabled = true;
        $("div#summary_notice").html(data.summary);
      } else{
        document.getElementById("summary_btn").disabled = false;
        $("div#summary_notice").html("");
      }
    });
    return false;
  }
$(function() {
  // The function is triggered on page load
  render_summary_notice()
});
function show_value(name, value) {
  // This function is used in the form in the options.html file
  // get the name of the element to control and the value that should be displayed
 document.getElementById(name).innerHTML=value;
};
