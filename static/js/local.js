
  $(function () {
	  /***** Loader *****/
	  setTimeout(function() {($('#loading').hide(), $('#screen').remove())}, 1 * 1000);
	  $(document).ajaxStart(function () {
		  $('#screen').show(),
		  $('#loading').show()
	  }).ajaxStop(function () {
		  $('#screen').hide(),
		  $('#loading').hide()
	  });

	  /***** Initialization, variables, and helper functions *****/
	  $('main').hide();
	  $('#table-header').hide();
	  $('#table-medicare').hide();
	  $('#table-medicaid').hide();
	  $('#infobox-pa-true').hide();
	  $('#infobox-pa-false').hide()
	  $('#color-codes').hide();
	  var medicareSelected;
	  var medicaidSelected;
	  var zipcode = '';
	  var plan = '';
	  var drug = '';
	  var drugHasPA = true;

	  $.fn.toggleButtonOn = function()
	  {
		  $(this).css("background-color", "#8cc63e"),
	      $(this).css("border-color", "#8cc63e")
	  };

	  $.fn.toggleButtonOff = function()
	  {
		  $(this).css("background-color", "#0069a3"),
	      $(this).css("border-color", "#0069a3")
	  };
	  /***** Autocomplete functionality *****/
      $("#input-plan-medicare").autocomplete({
		  source: function( request, response )
		  {
			  zipcode = $("#input-zipcode").val();
			  $.ajax(
				  {
					  url: "/plans",
					  dataType: "json",
					  data: {qry: request.term, zipcode: zipcode},
					  success: function( data )
					  {
						  response( data )
					  }
				  });
		  }
	  });

      $( "#input-med" ).autocomplete({
		  source: function( request, response )
		  {
			  $.ajax(
				  {
					  url: "/drug_names",
					  dataType: "json",
					  data: {qry: request.term },
					  success: function( data )
					  {
						  response( data )
					  }
				  });
		  }
	  });
	  /***** Medicare/medicaid button toggles *****/

	  $('#button-medicare').click(function ()
      {
		  medicareSelected = true;
		  medicaidSelected = false;
		  $('#button-medicare').toggleButtonOn();
		  $('#button-medicaid').toggleButtonOff();
		  $('main').show();
		  $('#form-zipcode').show();
		  $('#container-selected-zipcode').show();
		  $('#input-plan-medicare').show();
		  $('#input-plan-medicaid').hide();
		  $('html').clearAllInput();
	  });

	  $('#button-medicaid').click(function ()
      {
		  medicaidSelected = true;
		  medicareSelected = false;
		  $('#button-medicaid').toggleButtonOn();
		  $('#button-medicare').toggleButtonOff();
		  $('main').show();
		  $('#form-zipcode').hide();
		  $('#container-selected-zipcode').hide();
		  $('#input-plan-medicare').hide();
		  $('#input-plan-medicaid').show();
		  $('html').clearAllInput();
	  });

	  /***** Go buttons *****/
	  $('#button-go-zipcode').click(function ()
      {
		  var input = $('#input-zipcode').val()
		  if (input.length == 5 && $.isNumeric(input))
		  {
			  zipcode = input;
			  $('#selected-zipcode').html(zipcode)
		  } else
		  {
			  alert("Error: Enter a valid zipcode.");
		  }
	  })

	  $('#button-go-plan').click(function ()
	  {
		  var input;
		  if (medicareSelected)
		  {
			  input = $('#input-plan-medicare').val();
		  } else
		  {
			  input = $('#input-plan-medicaid').val();
		  }
		  if (input.length > 0)
		  {
			  plan = input;
			  $('#selected-plan').html(plan);
		  } else
		  {
			  alert("Error: Select a plan.");
		  }
	  })

	  $('#button-go-med').click(function ()
	  {
		  var input = $('#input-med').val();
		  if (input.length > 0)
		  {
			  drug = input;
			  $('#selected-med').html(drug);
		  } else
		  {
			  alert("Error: Select a medication.");
		  }
	  })

	  /***** Generate formulary insight *****/
	  generateMedicareResults = function ()
	  {
		  $.ajax
		  ({
			  url: "/medicare_options",
			  async: false,
			  dataType: "json",
			  data: {zipcode: zipcode, drug_name: drug, plan_name: plan},
			  success: function( resp )
			  {
				  
				  
				  
				  $("#medicarebody").empty();
				  for( d=0; d < resp.length; d++)
				  {
					  var tr =
						  (
						  '<tr>' +
						  '<td>' + '</td>' +
						  '<td>' + '</td>' +
						  '<td>' + '</td>' +
						  '<td>' + '</td>' +
						  '<td>' + '</td>' +
						  '<td>' + '</td>' +
						  '<td>' + '</td>' +
						  '</tr>'
						  );
					  $("#medicarebody").append(tr)

				  }
				  $('#table-header').show();
				  $('#table-medicare').show();
			  }
		  });
	  }

	  generateMedicaidResults = function ()
	  {
		  $.ajax
		  ({
			  url: "/medicaid_options",
			  async: false,
			  dataType: "json",
			  data: {drug_name: drug, plan_name: plan},
			  success: function( resp )
			  {
				  $('#medicaidhead').empty();
				  var headings = Object.keys(resp[0]);
				  var header = "<tr>";
				  
				  for( h=0; h<headings.length; h++)
				  {
					  header += '<th scope="col">'+headings[h]+'</th>';
				  }
				  header += '</tr>';
				  $('#medicaidhead').append(header);
				  
				  $('#medicaidbody').empty();
				  for( d=0; d < resp.length; d++)
				  {
					  if( resp[d]['Formulary Restrictions'].search('PA') )
					    cls = '<td class="table-success">';
					  else
					    cls = '<td class="table-danger">';

					 if ( resp[d][0] == false )
					    drugHasPA = false;
					 else
					    drugHasPA = true;

					  var tr = '<tr id="medicaid-success">' 
					  for ( h=0; h<headings.length; h++)
					  {
						  tr += cls + resp[d][headings[h]]+ '</td>' 
					  }
					  $('#medicaidbody').append(tr);
				  }

				  $('#table-medicaid').show();
				  $('#table-header').show();

				  if (drugHasPA)
				    $('#infobox-pa-false').show();
				  else
				    $('#infobox-pa-true').show();

				  $('#color-codes').show();
			  }
		  });
	  }

	  $('#button-generate').click(function ()
      {
		  if ((medicareSelected && zipcode.length == 0) || (plan.length == 0 || drug == 0))
		  {
			  alert("Error: One or more fields is missing. Make sure you have pressed the \"Add\" button after each field.");
		  } else
		  {
			  $('#table-header').text(drug);
			  if (medicareSelected)
			  {
				  generateMedicareResults();
			  } else
			  {
				  generateMedicaidResults();
			  }
			  $('#table-header').show();
		  }
	  })

	  /***** Clear buttons *****/
	  $.fn.clearAllInput = function ()
	  {
		  $('#table-header').hide(),
		  $('#table-medicare').hide(),
		  $('#table-medicaid').hide(),
		  $('#input-zipcode').val(''),
		  $('#input-plan-medicare').val(''),
		  $('#input-plan-medicaid').val(''),
		  $('#input-med').val(''),
		  zipcode = '',
		  plan = '',
		  drug = '',
		  $('#selected-zipcode').html(''),
		  $('#selected-plan').html(''),
		  $('#selected-med').html('')
	  }
	  $('#button-clear-med').click(function ()
      {
		  $('#input-med').val(''),
		  drug = '',
		  $('#selected-med').html('')
	  })
	  $('#button-clear-all').click(function ()
      {
		  $('main').hide(),
		  $('html').clearAllInput();
		  if (medicareSelected)
		  {
			  $('#button-medicare').toggleButtonOff(),
			  medicareSelected = false
		  } else
		  {
			  $('#button-medicaid').toggleButtonOff()
			  medicaidSelected = false
		  }
	  })
  });
