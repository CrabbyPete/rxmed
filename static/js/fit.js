  $(function () {
	  /***** Initialization, variables, and helper functions *****/

	  $('main').hide();
	  $('#loading-img').hide();
	  $('#table-header').hide();
	  $('#table-medicare').hide();
	  $('#table-medicaid').hide();
	  $('#table-medicaid').tablesorter();
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
      
      $( "#input-ndc" ).autocomplete({
		  source: function( request, response )
		  {
			  $.ajax(
				  {
					  url: "/ndc_drugs",
					  dataType: "json",
					  data: {qry: request.term },
					  success: function( data )
					  {
						  response( data )
					  }
				  });
		  }
	  });

      $( "#input-med" ).autocomplete({
    	  minLength: 2,
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
			  beforeSend: function() {
				  $('#loading-img').show();
			  },
			  success: function( resp )
			  {
				  $('#loading-img').hide();
				  
				  $("#medicarebody").empty();
				  for( d=0; d < resp.length; d++)
				  {
					  if( resp[d]['PA'].search('Yes') )
						    cls = '<td class="table-success">';
						  else
						    cls = '<td class="table-danger">';
						  	drugHasPA = true
					  
					  
					  var tr =
						  (
						  '<tr>' +
						  cls+resp[d]['Brand']+'</td>' +
						  cls+resp[d]['Generic']+'</td>' +
						  cls+resp[d]['Tier']+'</td>' +
						  cls+resp[d]['ST']+'</td>' +
						  cls+resp[d]['QL']+'</td>' +
						  cls+resp[d]['PA']+'</td>' +
						  cls+resp[d]['CopayP']+'</td>' +
						  cls+resp[d]['CopayD']+'</td>' +
						  '</tr>'
						  );
					  $("#medicarebody").append(tr)
				  }
				  $('#table-header').show();
				  $('#table-medicare').show();
			  },
			  error:function(resp)
			  {
				  console.log(resp);
				  $('#loading-img').hide();
			  }
		  });
	  }

	  generateMedicaidResults = function ()
	  {
		  $.ajax
		  ({
			  url: "/medicaid_options",
			  async: true,
			  dataType: "json",
			  data: {drug_name: drug, plan_name: plan},
			  beforeSend: function() {
				  $('#loading-img').show();
				  $('#loading-img')[0].scrollIntoView();
			  },
			  success: function( resp )
			  {
			  	  $('#loading-img').hide();
				  $('#medicaidhead').empty();

				  var heading = resp['heading'];
				  var header = "<tr>";
				  for( h=0; h < heading.length; h++)
				  {
					  header += '<th scope="col">'+heading[h]+'</th>';
				  }

				  header += '</tr>';
				  $('#medicaidhead').append(header);
				  $('#medicaidbody').empty();

				  if (resp['pa'] == true)
				    drugHasPA = true;
				  else
				    drugHasPA = false;

                  var data = resp['data']
                  var cls;
                  var tr;
				  for(var d=0; d < data.length; d++)
				  {
				    if( data[d]['Formulary Restrictions'].includes('PA') )
				    {
					    cls = '<td class="table-danger">';
					    tr  = '<tr class="table-danger">';
					}
					else
					{
					    cls = '<td class="table-success">';
					    tr  = '<tr class="table-success">';
                    }

					for ( h=0; h<heading.length; h++)
					{
				        tr += cls + data[d][heading[h]]+ '</td>'
					}
                    tr += '</tr>'
					$('#medicaidbody').append(tr);
				  }

				  $('#table-medicaid').show();
				  $('#table-header').show();

				  if (drugHasPA)
				  {
				    $('#infobox-pa-true').show();
				    $('#infobox-pa-false').hide();
				  }
				  else
				  {
				    $('#infobox-pa-false').show();
				    $('#infobox-pa-true').hide();
                  }
				  $('#color-codes').show();

				  var resort = true;
                  $('table-medicaid').trigger("update", [resort]);

				  /*
				  $('#table-medicaid').DataTable({
				                                    paging: false,
				                                    searching:false
				  });
				  */
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
		  $('#infobox-pa-false').hide(),
		  $('#infobox-pa-true').hide(),
	      $('#color-codes').hide()
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