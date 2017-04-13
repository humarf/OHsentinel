<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:svc="urn:schemas-upnp-org:service-1-0">
<!--:deploy:OHsentinel:/usr/local/share/OHsentinel/xsl:-->
	<xsl:output method="text" encoding="utf-8" indent="no" omit-xml-declaration="yes"/>
	<xsl:strip-space elements="*"/>
	<xsl:param name="action" select="'list_actions'"/>
	<xsl:param name="type" select="''"/>

	<xsl:template match="/svc:scpd">
		<xsl:choose>
			<xsl:when test="$action = 'list_actions'">
				<xsl:for-each select="svc:actionList/svc:action">
					<xsl:value-of select="svc:name" />
					<xsl:value-of select="','" />
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$action = 'in' or $action = 'out'">
				<xsl:for-each select="svc:actionList/svc:action">
					<xsl:if test="svc:name/text() = $type">
						<xsl:for-each select="svc:argumentList/svc:argument">
							<xsl:if test="svc:direction/text() = $action">
								<xsl:value-of select="svc:name/text()" />
								<xsl:value-of select="','" />
							</xsl:if>
						</xsl:for-each>
					</xsl:if>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$action = 'in_state_var'">
				<xsl:for-each select="svc:actionList/svc:action">
					<xsl:if test="svc:name/text() = $type">
						<xsl:for-each select="svc:argumentList/svc:argument">
							<xsl:if test="svc:direction/text() = 'in'">
								<xsl:value-of select="svc:name/text()" />
								<xsl:value-of select="'='" />
								<xsl:value-of select="svc:relatedStateVariable/text()" />
								<xsl:value-of select="','" />
							</xsl:if>
						</xsl:for-each>
					</xsl:if>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$action = 'out_state_var'">
				<xsl:for-each select="svc:actionList/svc:action">
					<xsl:if test="svc:name/text() = $type">
						<xsl:for-each select="svc:argumentList/svc:argument">
							<xsl:if test="svc:direction/text() = 'out'">
								<xsl:value-of select="svc:name/text()" />
								<xsl:value-of select="'='" />
								<xsl:value-of select="svc:relatedStateVariable/text()" />
								<xsl:value-of select="','" />
							</xsl:if>
						</xsl:for-each>
					</xsl:if>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$action = 'list_variables'">
				<xsl:for-each select="svc:serviceStateTable/svc:stateVariable">
					<xsl:value-of select="svc:name" />
					<xsl:if test="$type = 'explore'">
						<xsl:value-of select="'='" />
						<xsl:value-of select="@sendEvents" />
						<xsl:value-of select="'='" />
						<xsl:value-of select="svc:dataType" />
					</xsl:if>	
					<xsl:value-of select="','" />
				</xsl:for-each>
			</xsl:when>
		</xsl:choose>
	</xsl:template>
	
	<xsl:template match="text()">
	</xsl:template>
</xsl:stylesheet>
