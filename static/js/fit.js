  $(function () {
	  /***** Initialization, variables, and helper functions *****/

	  $('main').hide();
	  $('#loading-img').hide();
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
	  var medicaid_table = $('#table-medicaid').DataTable({paging:false, searching:false, info:false});
	  var medicare_table = $('#table-medicare').DataTable({paging:false, searching:false, info:false});
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
			  dataType: "json",
			  data: {zipcode: zipcode, drug_name: drug, plan_name: plan},
			  beforeSend: function() {
				  $('#loading-img').show();
			  },
			  success: function( resp )
			  {
				  $('#loading-img').hide();
				  medicare_table.destroy();

				  if (resp['pa'] == true)
				    drugHasPA = true;
				  else
				    drugHasPA = false;

				  $("#medicarebody").empty();
				  for( var d=0; d < resp['data'].length; d++)
				  {
					  if( resp['data'][d]['PA'].search('Yes') )
						    cls = '<td class="table-success">';
						  else
						    cls = '<td class="table-danger">';

					  var tr =
						  (
						  '<tr>' +
						  cls+resp['data'][d]['Brand']+'</td>' +
						  cls+resp['data'][d]['Generic']+'</td>' +
						  cls+resp['data'][d]['Tier']+'</td>' +
						  cls+resp['data'][d]['ST']+'</td>' +
						  cls+resp['data'][d]['QL']+'</td>' +
						  cls+resp['data'][d]['PA']+'</td>' +
						  cls+resp['data'][d]['CopayD']+'</td>' +
						  cls+resp['data'][d]['CTNP']+'</td>' +
						  '</tr>'
						  );
					  $("#medicarebody").append(tr)
				  }

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


				  $('#table-header').show();
				  $('#table-medicare').show();
				  medicare_table = $('#table-medicare').DataTable({paging:false, searching:false, info:false});
			  }
		  });
	  }

	  generateMedicaidResults = function ()
	  {
		  $.ajax
		  ({
			  url: "/medicaid_options",
			  dataType: "json",
			  data: {drug_name: drug, plan_name: plan},
			  beforeSend: function() {
				  $('#loading-img').show();
				  $('#loading-img')[0].scrollIntoView();
			  },
			  success: function( resp )
			  {
			  	  $('#loading-img').hide();
			  	  medicaid_table.destroy();

				  $('#medicaidhead').empty();
				  $('#medicaidbody').empty();

				  var heading = resp['heading'];
				  var header = "<tr>";
				  for( var h=0; h < heading.length; h++)
				  {
					  if ( heading[h] != 'PA Reference')
					    header += '<th scope="col">'+heading[h]+'</th>';
				  }

				  header += '</tr>';
				  $('#medicaidhead').append(header);

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

					for (var h=0; h<heading.length; h++)
					{
				        if ( heading[h] == 'PA Reference')
				            continue


				        if (h==0 && 'PA Reference' in data[d] && data[d]['PA Reference'].length > 5)
				        {
				            tr += cls + '<a href="'+ data[d]['PA Reference']+'">';
				            tr += data[d][heading[h]];
				            tr += '</a></td>';
				        }
				        else
				            tr += cls + data[d][heading[h]]+ '</td>';
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

				  medicaid_table = $('#table-medicaid').DataTable({paging:false, searching:false, info:false});
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
			  $('#display_results').show()
		  }
	  })

	  $('#button-clear-med').click(function ()
      {
		  $('#input-med').val('');
		  drug = '';
		  $('#display_results').hide();
	  })

	  $('"button-clear-all"').click(function ()
      {
		  $('#input-med').val('');
		  $('#input-zipcode').val('');
		  $('input-plan-medicare').val('');
		  drug = '';
		  $('#display_results').hide();
	  })
  });