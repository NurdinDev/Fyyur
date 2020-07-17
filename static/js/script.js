window.parseISOString = function parseISOString(s) {
	var b = s.split(/\D+/);
	return new Date(Date.UTC(b[0], --b[1], b[2], b[3], b[4], b[5], b[6]));
};


window.deleteVenue = function deleteVenue(id) {
	fetch('/venues/' + id, {
		method: 'DELETE'
	}).then(function (response) {
		if (!response.ok) {
			throw Error(response.statusText);
		}
		return response;
	}).then(function (response) {
		console.log("OK", response);
		window.location.href = '/';
	}).catch(function (error) {
		console.log(error);
	})
}
