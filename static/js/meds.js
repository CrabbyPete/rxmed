  $(function () {
	  var zipcode = '';
	  var plan = '';
	  var drug = '';


	  //<input class="form-control ui-autocomplete-input" id="input-plan-medicare" name="plan" placeholder="Type to search..." style="height: 38px;" type="text" value="" autocomplete="off">
      // Clear the plan if they switch type
      $("#plan_type-0").click(function(){
        $('input[name=plan]').val('');
      })

      $("#plan_type-1").click(function(){
        $('input[name=plan]').val('');
      })

      $("#plan_type-2").click(function(){
        $('input[name=plan]').val('');
      })

      $("#button-clear-med").click(function(){
        $('input[name=medication]').val('');
      })

	  /***** Autocomplete functionality *****/
      $("#input-plan-medicare").autocomplete({
		  source: function( request, response )
		  {
			  var zipcode = $("#input-zipcode").val();
			  var plan = $('input[name=plan_type]:checked').val()
			  $.ajax(
				  {
					  url: "/plans",
					  dataType: "json",
					  data: {qry: request.term, zipcode: zipcode, plan:plan},
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
  });